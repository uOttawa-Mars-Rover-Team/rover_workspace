#!/bin/bash

ROVER_WS=/home/uorover/rover_workspace

sudo chmod -R 777 $ROVER_WS/../.ros
sudo chmod -R a+w $ROVER_WS
sudo chown -R $(whoami) $ROVER_WS/..

cd $ROVER_WS
# Rosdep will read each package in src/ and install dependencies listed in each
# package's package.xml file
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
