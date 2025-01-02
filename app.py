from flask import Flask, jsonify, request, Response
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlencode
from dotenv import load_dotenv
import os
import glob
import gzip
import base64

load_dotenv()

LOG_FILE = os.getenv("LOG_FILE")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
PORT = os.getenv("PORT")
HOST = os.getenv("HOST")

app = Flask(__name__)

def get_all_log_files(base_log_file):
    log_files = glob.glob(base_log_file + "*")
    log_files_sorted = sorted(log_files, key=lambda x: os.path.getmtime(x), reverse=True)
    return log_files_sorted

def open_log_file(file_path):
    if file_path.endswith('.gz'):
        return gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore')
    else:
        return open(file_path, 'r', encoding='utf-8', errors='ignore')

def parse_logs(page=1, per_page=200):
    uri_data = defaultdict(lambda: {"hits": 0, "last_accessed": None})

    try:
        # Read all relevant log files
        log_files = get_all_log_files(LOG_FILE)
        for log_file in log_files:
            with open_log_file(log_file) as file:
                for line in file:
                    parts = line.split('"')

                    if len(parts) > 1:
                        try:
                            uri = parts[1].strip().split(' ')[1]
                            if uri.endswith('.jpg') or uri.endswith('.jpeg') or uri.endswith('.png') or uri.endswith('.JPEG') or uri.endswith('.svg') or uri.endswith('.PNG') or uri.endswith('.JPG') or uri.endswith('.JPEG') or uri.endswith('.json') or uri.endswith('.ico'):
                                continue

                            if uri.endswith('robots.txt') or uri.endswith('/wordpress'):
                                continue

                            if uri.find('.well-known') != -1:
                                continue

                            if uri.find('.php') != -1:
                                continue

                            if uri.endswith('.env') or uri.endswith('.git/config'):
                                continue

                            raw_date = line.split('[')[1].split(']')[0]
                            last_accessed = datetime.strptime(
                                raw_date.split(' ')[0], "%d/%b/%Y:%H:%M:%S"
                            )

                            if (
                                uri_data[uri]["last_accessed"] is None
                                or last_accessed > uri_data[uri]["last_accessed"]
                            ):
                                uri_data[uri]["last_accessed"] = last_accessed

                            uri_data[uri]["hits"] += 1
                        except (IndexError, ValueError):
                            continue  # Skip malformed lines

    except FileNotFoundError:
        return {"error": "Log file not found"}, 404

    # Sort the data
    sorted_data = sorted(
        uri_data.items(),
        key=lambda x: (x[1]["hits"], x[1]["last_accessed"]),
        reverse=True,
    )

    # Pagination
    total = len(sorted_data)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = sorted_data[start:end]

    result = [
        {
            "uri": uri,
            "hits": data["hits"],
            "last_accessed": data["last_accessed"].strftime("%Y-%m-%d %H:%M:%S"),
        }
        for uri, data in paginated_data
    ]

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }

    return {
        "pagination": pagination,
        "data": result,
    }, 200

def check_auth(username, password):
    return username == USERNAME and password == PASSWORD

def authenticate():
    return Response(
            "Authentication required", 401,
            {"WWW-Authenticate": 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/log-report', methods=['GET'])
@requires_auth
def log_report():
    try:
        # Retrieve pagination parameters with defaults
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 200))
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    data, status = parse_logs(page, per_page)
    if isinstance(data, dict) and "error" in data:
        return jsonify(data), status

    pagination = data["pagination"]
    result = data["data"]

    base_url = request.base_url

    def build_url(page_number):
        query_params = request.args.to_dict()
        query_params['page'] = page_number
        query_params['per_page'] = per_page
        return f"{base_url}?{urlencode(query_params)}"

    links = {}
    if pagination["has_next"]:
        links["next"] = build_url(pagination["page"] + 1)
    if pagination["has_prev"]:
        links["previous"] = build_url(pagination["page"] - 1)

    response = {
        "pagination": pagination,
        "links": links,
        "data": result,
    }

    return jsonify(response)
if __name__ == "__main__":
    if not all([LOG_FILE, USERNAME, PASSWORD, PORT, HOST]):
        raise ValueError("One or more environment variables are missing")

    app.run(host=HOST, port=PORT)

