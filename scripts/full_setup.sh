#!/bin/bash

set -e

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

echo -e "\e[1m             ____   _____     _______ ____
 _   _  ___ |  _ \ / _ \ \   / / ____|  _ \
| | | |/ _ \| |_) | | | \ \ / /|  _| | |_) |
| |_| | (_) |  _ <| |_| |\ V / | |___|  _ <
 \__,_|\___/|_| \_\\\\\\___/  \_/  |_____|_| \_\ \e[0m\n"
echo -e "Setting up your development environment of uOttawa Mars Rover's workspace...\n\n"

echo "Workspace:  $ROVER_WS"
echo "OS:         Ubuntu $UBUNTU_CODENAME ($ARCH)$(is_jetson && echo ", NVIDIA Jetson")"
echo -e "ROS distro: $ROVER_ROS_DISTRO\n"

"$SCRIPTS_DIR/install_ros.sh"
"$SCRIPTS_DIR/install_external_packages.sh"
"$SCRIPTS_DIR/build_project.sh"

complete
title "FULL SETUP IS COMPLETE. PLEASE CLOSE ALL TERMINAL WINDOWS."
