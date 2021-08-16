#!/bin/bash

complete () { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title () { echo -e "\e[1m\e[44m $1 \e[0m"; }

title "---- Seting up ROS melodic ----"

title "Setting up sources.list"
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list';
complete

title "Setting up keys"
sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654;
complete

title "Configuring Ubuntu repositories to allow restricted, universe, and multiverse"
sudo add-apt-repository restricted;
sudo add-apt-repository universe;
sudo add-apt-repository multiverse;
complete

title "Installing ROS melodic"
sudo apt update;
sudo apt -y install ros-melodic-desktop-full ros-melodic-openslam-gmapping python-rosdep;
complete

title "Initializing rosdep"
sudo rosdep init;
rosdep update;
complete

title "Sourcing .bashrc - Environment setup"
echo "source /opt/ros/melodic/setup.bash" >> ~/.bashrc;
echo "source ~/rover_workspace/devel/setup.bash" >> ~/.bashrc;
source ~/.bashrc;
complete
