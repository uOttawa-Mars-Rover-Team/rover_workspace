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
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb" # If using Ubuntu derivates use $UBUNTU_CODENAME
sudo dpkg -i /tmp/ros2-apt-source.deb
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
SOURCE_CMD="[ -f ${SCRIPT_PATH} ] && source ${SCRIPT_PATH}"
echo $SOURCE_CMD >>~/.bashrc
source ~/.bashrc
completed
