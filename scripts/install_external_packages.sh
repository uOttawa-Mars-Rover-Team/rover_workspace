#!/bin/bash

set -e

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }
ROVER_WS=~/rover_workspace

title "----- Installing external packages -----"

title "Installing Node.js"
# Installation instructions should match the ones listed in the dashboard's
# README.md
echo "Adding Node.js PPA and installing Node.js v22 (for dashboard)"
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install -y curl
curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
sudo -E bash nodesource_setup.sh
sudo apt-get install -y nodejs
complete

title "Installing pip (for Python)"
sudo apt-get update
sudo apt-get upgrade
sudo apt install -y python3-pip
complete

title "Installing project ROS dependencies using rosdep"
cd $ROVER_WS
# Rosdep will read each package in src/ and install dependencies listed in each
# package's package.xml file
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths src -i -r -y --rosdistro humble
complete
