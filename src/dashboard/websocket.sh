#!/bin/bash

# Check if the rosbridge_server package is installed
ros2 pkg list | grep "rosbridge_server" &> /dev/null
if ! [ $? == 0 ]; then
	# Install rosbridge_server if necessary
	sudo apt-get update && sudo apt-get install -y ros-humble-rosbridge-server
fi
ros2 launch rosbridge_server rosbridge_websocket_launch.xml port:=9090
