#!/usr/bin/env bash

set -e

source /opt/ros/humble/setup.bash
source ~/rover_workspace/install/setup.bash && ros2 launch chassis_controls rover.launch.py
