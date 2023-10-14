#!/bin/bash

complete() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }

echo -e "\e[1m             ____   _____     _______ ____  
 _   _  ___ |  _ \ / _ \ \   / / ____|  _ \ 
| | | |/ _ \| |_) | | | \ \ / /|  _| | |_) |
| |_| | (_) |  _ <| |_| |\ V / | |___|  _ < 
 \__,_|\___/|_| \_\\\\\\___/  \_/  |_____|_| \_\ \e[0m\n"
echo -e "Setting up your development environment of uOttawa Mars Rover's workspace...\n\n"

./install_ros_humble.sh
./install_external_packages.sh
./build_project.sh

complete
title "FULL SETUP IS COMPLETE. PLEASE CLOSE ALL TERMINAL WINDOWS."
