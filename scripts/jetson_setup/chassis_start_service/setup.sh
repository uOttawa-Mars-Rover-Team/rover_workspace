#!/usr/bin/env bash

set -e

# Get the directory where the script itself is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the service file into /etc/systemd/system/
sudo cp "$SCRIPT_DIR/chassis-start.service" /etc/systemd/system/chassis-start.service

# Copy the chassis-start.sh file into /usr/local/bin/
sudo cp "$SCRIPT_DIR/chassis-start.sh" /usr/local/bin/chassis-start.sh

# Reload systemd so it sees new service files
sudo systemctl daemon-reload

bash "$SCRIPT_DIR/enable.sh"

echo "The chassis-start service has been setup and enabled to run on boot. To disable running on boot, please run disable.sh"
