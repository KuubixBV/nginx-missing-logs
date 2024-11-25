#!/bin/bash

echo "Setting up your Flask app with a virtual environment and optional systemd service..."

# Step 1: Create a venv
echo "Creating virtual environment..."
python3 -m venv venv || { echo "Failed to create virtual environment. Ensure Python 3 is installed."; exit 1; }
echo "Virtual environment created."

# Step 2: Activate venv and install requirements
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || { echo "Failed to install requirements."; exit 1; }
else
    echo "No requirements.txt found. Skipping dependency installation."
fi
deactivate
echo "Dependencies installed."

# Step 3: Ask to create a systemd service
read -p "Do you want to create a systemd service for this Flask app? (yes/no): " create_service
if [[ "$create_service" == "yes" ]]; then
    read -p "Enter the systemd service name (e.g., flask-log-report): " service_name
    read -p "Enter the user to run the service (default: $USER): " service_user
    service_user=${service_user:-$USER}  # Default to current user if empty
    read -p "Enter the directory of the Flask app (default: current directory): " app_directory
    app_directory=${app_directory:-$(pwd)}  # Default to current directory if empty

    service_file="/etc/systemd/system/$service_name.service"
    sudo bash -c "cat > $service_file" <<EOL
[Unit]
Description=Flask App: $service_name
After=network.target

[Service]
User=$service_user
WorkingDirectory=$app_directory
Environment="PYTHONUNBUFFERED=1"
ExecStart=$app_directory/venv/bin/python $app_directory/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

    echo "Systemd service file created at $service_file."

    # Enable and start the service
    sudo systemctl daemon-reload
    sudo systemctl enable $service_name
    sudo systemctl start $service_name
    echo "Systemd service $service_name has been enabled and started."
else
    echo "Skipping systemd service setup."
fi

echo "Setup completed!"

