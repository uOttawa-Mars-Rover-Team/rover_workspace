#!/bin/bash

set -e

completed() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }

ROVER_WS=~/rover_workspace

title "---- Installing and setting up ROS2 Humble ----"

title "Updating and upgrading existing packages"
sudo apt-get update
sudo apt-get -y upgrade
completed

title "Setting up sources"
sudo apt install -y software-properties-common
sudo add-apt-repository -y universe

sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
completed

title "Updating and upgrading existing packages (after ROS repo installation)"
sudo apt-get update
sudo apt-get -y upgrade
completed

title "Installing ROS2 Humble"
sudo apt install -y ros-humble-desktop
sudo apt install -y ros-dev-tools
completed

title "Installing and initializing rosdep"
sudo apt-get -y install python3-rosdep
sudo rosdep init
rosdep update
completed

title "Sourcing .bashrc - Environment setup"
echo "source /opt/ros/humble/setup.bash" >>~/.bashrc
SCRIPT_PATH="~/rover_workspace/install/setup.bash"
SOURCE_CMD="[ -f ~/rover_workspace/install/setup.bash ] && source ${SCRIPT_PATH}"
echo $SOURCE_CMD >>~/.bashrc
source ~/.bashrc
completed
