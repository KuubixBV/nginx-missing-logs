from flask import Flask, jsonify, request, Response
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
import base64

load_dotenv()

LOG_FILE = os.getenv("LOG_FILE")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
PORT = os.getenv("PORT")
HOST = os.getenv("HOST")

app = Flask(__name__)

def parse_logs():
    uri_data = defaultdict(lambda: {"hits": 0, "last_accessed": None})

    try:
        with open(LOG_FILE, "r") as file:
            lines = file.readlines()

        for line in lines:
            parts = line.split('"')

            if len(parts) > 1:
                uri = parts[1].strip().split(' ')[1]

                raw_date = line.split('[')[1].split(']')[0]
                last_accessed = datetime.strptime(raw_date.split(' ')[0], "%d/%b/%Y:%H:%M:%S")

                if uri_data[uri]["last_accessed"] is None or last_accessed > uri_data[uri]["last_accessed"]:
                    uri_data[uri]["last_accessed"] = last_accessed

                uri_data[uri]["hits"] += 1

    except FileNotFoundError:
        return {"error": "Log file not found"}

    sorted_data = sorted(
        uri_data.items(),
        key=lambda x: (x[1]["last_accessed"], x[1]["hits"]),
        reverse=True
    )

     result = [
        {
            "uri": uri,
            "hits": data["hits"],
            "last_accessed": data["last_accessed"].strftime("%Y-%m-%d %H:%M:%S")
        }
        for uri, data in sorted_data
    ]

    return result

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
    data = parse_logs()
    if isinstance(data, dict) and "error" in data:
        return jsonify(data), 404
    return jsonify(data)

if __name__ == "__main__":
    if not all([LOG_FILE, USERNAME, PASSWORD, PORT, HOST]):
        raise ValueError("One or more environment variables are missing")

    app.run(host=HOST, port=PORT)

