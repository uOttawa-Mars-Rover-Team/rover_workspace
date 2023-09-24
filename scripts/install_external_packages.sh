#!/bin/bash

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }
ROVER_WS=~/rover_workspace

title "----- Installing external packages -----"

# Installation instructions should match the ones listed in the dashboard's
# README.md
echo "Adding Node.js PPA and installing Node.js v18 (for dashboard)"
sudo apt update
sudo apt upgrade
cd ~
curl -sL https://deb.nodesource.com/setup_18.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt install nodejs
rm nodesource_setup.sh
complete

title "Installing project ROS dependencies using rosdep"
cd $ROVER_WS
# Rosdep will read each package in src/ and install dependencies listed in each
# package's package.xml file
sudo rosdep install --from-paths src --ignore-src -r -y
complete
