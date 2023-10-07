#!/bin/bash

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }
ROVER_WS=~/rover_workspace

title "----- Installing external packages -----"

# Installation instructions should match the ones listed in the dashboard's
# README.md
echo "Adding Node.js PPA and installing Node.js v18 (for dashboard)"
sudo apt-get update
sudo apt-get upgrade
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
NODE_MAJOR=18
echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list
sudo apt-get update
sudo apt-get install nodejs -y
complete

title "Installing pip (for Python)"
sudo apt update
sudo apt install python3-pip
complete

title "Installing colcon"
sudo sh -c 'echo "deb [arch=amd64,arm64] http://repo.ros2.org/ubuntu/main `lsb_release -cs` main" > /etc/apt/sources.list.d/ros2-latest.list'
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install python3-colcon-common-extensions
complete

title "Installing project ROS dependencies using rosdep"
cd $ROVER_WS
# Rosdep will read each package in src/ and install dependencies listed in each
# package's package.xml file
rosdep update
sudo rosdep install --from-paths src --ignore-src -r -y
complete
