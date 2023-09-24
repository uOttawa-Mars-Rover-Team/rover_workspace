#!/bin/bash

completed() { echo -e "\e[1m\e[32mComplete.\e[0m\n"; }
title() { echo -e "\e[1m\e[44m $1 \e[0m"; }

ROVER_WS=~/rover_workspace

title "----- Building project -----"

title "Running colcon build"
source /opt/ros/humble/setup.bash
(cd $ROVER_WS && colcon build)
completed
