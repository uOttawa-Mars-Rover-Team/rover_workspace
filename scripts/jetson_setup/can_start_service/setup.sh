#!/usr/bin/env bash

set -e

# Get the directory where the script itself is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Copy the service file into /etc/systemd/system/
sudo cp "$SCRIPT_DIR/can-start.service" /etc/systemd/system/can-start.service

# Copy the can_start.sh file from the chassis_controls package into /usr/local/bin/
sudo cp "$SCRIPT_DIR/../../../src/chassis_controls/scripts/can_start.sh" /usr/local/bin/can-start.sh

# Reload systemd so it sees new service files
sudo systemctl daemon-reload
# Enable on boot
sudo systemctl enable can-start.service
# Start immediately
sudo systemctl start can-start.service

echo "The can-start service has been setup and enabled to run on boot."
