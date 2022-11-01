# ROS Package: teleop\_twist\_joy

## Info

__Topics:__ 
- /**joy**
- /**teleop/cmd_vel**
- /**cmd_vel**

__Scripts:__ 
- [src/teleop_twist_joy.cpp](src/teleop_twist_joy.cpp)
- [src/teleop_node.cpp](src/teleop_node.cpp)
- [src/cmd_vel_mux.py](src/cmd_vel_mux.py)
- [src/simple_drive.py](src/simple_drive.py)

__Maintainers:__ Aaron Knapper

__Prerequisite:__ This package requires ROS Joy to be installed `sudo apt-get install ros-melodic-joy`. (Although the package "joy" is now installed during the full_setup script runtime.)

__Extra Info:__  

## Description

There are four launch files to control the drive system. turtlesim-drive.launch is used for testing with turtlesim and remaps the \_cmd_vel message to \_turtle1\_cmd_vel. combined.launch runs all the nodes required to run the drive system. It can be run on the rover PC when the joystick is directly connected to the rover without the base station computer. During competition (or when the base station computer is used), roverPC.launch is run on the rover PC and baseStationPC.launch is run on the base station computer. The port the joystick is connected to can be changed in the launch scripts by updating the joy_dev argument near the top of the file. The drive\_firmware.ino from the Arduino sketches needs to be loaded onto the arduino connected to the motor controllers and connected to the rover computer.

Drive is a package that takes joystick input via **joy_node** and sends it as message **/joy** to the **teleop_twist_joy** node. This node calculates linear and angular velocities and advertises these values to the **/teleop/cmd_vel** topic.

From here **cmd_vel_mux** multiplexes between the messages **/teleop/cmd_vel** and **/move_base/cmd_vel**. The chosen topic is published to **/cmd_vel** and output to the **simple_drive** node which is sent to the drive wheel motor controllers.

## Helpful Resources:
This package is heavily influenced by the official teleop_twist_joy ROS package. Thanks Clearpath. Link: http://wiki.ros.org/teleop_twist_joy

Lastly the MUX aspect of this package was reused from the ROS Simple Drive. Thanks Ryerson. http://wiki.ros.org/simple_drive
