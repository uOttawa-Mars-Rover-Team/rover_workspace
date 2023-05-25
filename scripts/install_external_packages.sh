#!/bin/bash

complete () { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title () { echo -e "\e[1m\e[44m $1 \e[0m"; }

title "----- Installing external packages -----"

title "Cloning external packages repositories"
git submodule update --init --recursive;
complete

title "Installing Dependencies for the drive system"
sudo apt-get install -y ros-melodic-joy
complete

title "Installing dependencies for the external packages"
sudo apt -y install python-rosinstall python-rosinstall-generator python-wstool build-essential libusb-dev libspnav-dev;
complete

title "Installing external packages"
rosdep install --from-paths ../src/external_packages -i -y;
complete

echo "Remove the wii remote from joystick_drivers";
rm -rf ./src/external_packages/joystick_drivers/wiimote;
echo "Complete";
echo "";

echo "Adding Node.js PPA and installing Node.js (for dashboard)";
curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -;
sudo apt install -y nodejs;
echo "Complete";
echo "";

title "Installing APT external packages"
sudo apt -y install ros-melodic-openslam-gmapping ros-melodic-realsense2-camera ros-melodic-rtabmap-ros ros-melodic-video-stream-opencv ros-melodic-rviz ros-melodic-rosserial ros-melodic-joystick-drivers ros-melodic-web-video-server;
complete
>>>>>>> 821a30cd08e9504a54dbfcd0611eed5b881c3bfb
