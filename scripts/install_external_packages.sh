#!/bin/bash

complete () { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title () { echo -e "\e[1m\e[44m $1 \e[0m"; }

title "----- Installing external packages -----"

title "Cloning external packages repositories"
git submodule update --init --recursive;
complete

title "Installing dependencies for the external packages"
sudo apt -y install python-rosinstall python-rosinstall-generator python-wstool build-essential libusb-dev libspnav-dev;
complete

title "Installing external packages"
rosdep install --from-paths ../src/external_packages -i -y;
complete

title "Removing wii remote from joystick_drivers"
rm -rf ../src/external_packages/joystick_drivers/wiimote;
complete
