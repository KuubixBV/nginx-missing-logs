# Flask Log Report API

## Overview
This repository contains a Flask-based API for processing and analyzing web server logs. The API extracts and aggregates access data from log files, providing insights such as request counts and last accessed times, while filtering out unwanted entries (e.g., images, bot requests, and sensitive files). Authentication is required to access the log report.

## Features
- **Parses log files** to extract URI access counts and last accessed timestamps.
- **Filters irrelevant requests**, such as media files, bots, and sensitive files.
- **Supports pagination** with customizable `page` and `per_page` query parameters.
- **Basic Authentication** required to access the API.
- **Supports compressed log files** (`.gz`).
- **Setup script for virtual environment and optional systemd service**.

## Requirements
- Python 3.x
- Flask
- `python-dotenv` for environment variable management

### Install Dependencies
```bash
pip install flask python-dotenv
```

## Environment Variables
Create a `.env` file in the project directory and set the following variables:
```ini
LOG_FILE=/path/to/logfile
USERNAME=your_username
PASSWORD=your_password
PORT=5000
HOST=0.0.0.0
```

## Running the API
Start the Flask application with:
```bash
python app.py
```

## API Endpoints
### `GET /log-report`
Retrieves a paginated list of URI accesses from the log files.

#### Request Parameters:
- `page` (optional, default: `1`): The page number for pagination.
- `per_page` (optional, default: `200`): The number of results per page.

#### Authentication:
This endpoint requires **Basic Authentication** with the credentials defined in the `.env` file.

#### Response Format:
```json
{
  "pagination": {
    "page": 1,
    "per_page": 200,
    "total": 500,
    "total_pages": 3,
    "has_next": true,
    "has_prev": false
  },
  "links": {
    "next": "http://localhost:5000/log-report?page=2&per_page=200"
  },
  "data": [
    {
      "uri": "/home",
      "hits": 50,
      "last_accessed": "2024-02-12 14:30:00"
    }
  ]
}
```

## Authentication
The API uses **Basic Authentication**. Include your credentials in the request header:
```bash
curl -u your_username:your_password "http://localhost:5000/log-report?page=1&per_page=100"
```

## Error Handling
- `401 Unauthorized`: Incorrect or missing authentication.
- `400 Bad Request`: Invalid pagination parameters.
- `404 Not Found`: Log file not found.

## Setup Script
A `setup.sh` script is provided to streamline the setup process. It:
- Creates a virtual environment.
- Installs dependencies from `requirements.txt`.
- Optionally sets up a systemd service for running the Flask application as a background service.

### Running the Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

### Systemd Service (Optional)
The script will prompt you to set up a systemd service. If enabled, it will:
- Create a service file.
- Enable and start the service.

## Notes
- Ensure your log files are accessible and specified correctly in `.env`.
- The application will **not start** if required environment variables are missing.

## License
This project is open-source under the MIT License.
