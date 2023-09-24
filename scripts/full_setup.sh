#!/bin/bash

echo -e "\e[1m             ____   _____     _______ ____  
 _   _  ___ |  _ \ / _ \ \   / / ____|  _ \ 
| | | |/ _ \| |_) | | | \ \ / /|  _| | |_) |
| |_| | (_) |  _ <| |_| |\ V / | |___|  _ < 
 \__,_|\___/|_| \_\\\\\\___/  \_/  |_____|_| \_\ \e[0m\n"
echo -e "Setting up your development environment of uOttawa Mars Rover's workspace\n\n"

./install_ros_humble.sh
./install_external_packages.sh
./build_project.sh

echo "If you get an error saying catkin_make command not found, please copy/paste the next line in your terminal"
echo "source ~/.bashrc && cd .. && catkin_make"
