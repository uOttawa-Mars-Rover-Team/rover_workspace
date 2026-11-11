#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

title "----- Installing external packages -----"

title "Installing Node.js"
# Installation instructions should match the ones listed in the dashboard's
# README.md
echo "Adding Node.js PPA and installing Node.js v22 (for dashboard)"
apt_upgrade
sudo apt-get install -y curl
NODESOURCE_SETUP="$(mktemp)"
curl -fsSL https://deb.nodesource.com/setup_22.x -o "$NODESOURCE_SETUP"
sudo -E bash "$NODESOURCE_SETUP"
rm -f "$NODESOURCE_SETUP"
sudo apt-get install -y nodejs
complete

title "Installing pip (for Python)"
sudo apt-get install -y python3-pip
complete

title "Installing project ROS dependencies using rosdep"
cd "$ROVER_WS"
# Rosdep will read each package in src/ and install dependencies listed in each
# package's package.xml file
source "$ROS_SETUP"
rosdep update
rosdep install --from-paths src -i -r -y --rosdistro "$ROVER_ROS_DISTRO"
complete

if is_jetson; then
    title "Setting up rover hardware access (Jetson)"
    # can-utils gives candump/cansend for debugging the drive system's CAN bus
    sudo apt-get install -y can-utils iproute2
    # Serial-attached microcontrollers (/dev/ttyACM*, /dev/ttyUSB*) need dialout
    if ! id -nG "$USER" | grep -qw dialout; then
        sudo usermod -aG dialout "$USER"
        warn "Added $USER to the dialout group. Log out and back in for it to take effect."
    fi
    complete
fi
