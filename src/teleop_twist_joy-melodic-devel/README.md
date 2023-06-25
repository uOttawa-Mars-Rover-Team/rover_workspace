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

There are four launch files to control the drive system. turtlesim-drive.launch is used for testing with turtlesim and remaps the \_cmd_vel message to \_turtle1\_cmd_vel. combined.launch runs all the nodes required to run the drive system. It can be run on the rover PC when the joystick is directly connected to the rover without the base station computer. During competition (or when the base station computer is used), roverPC.launch is run on the rover PC and baseStationPC.launch is run on the base station computer. The port the joystick is connected to can be changed in the launch scripts by updating the joy_dev argument near the top of the file.

Drive is a package that takes joystick input via **joy_node** and sends it as message **/joy** to the **teleop_twist_joy** node. This node calculates linear and angular velocities and advertises these values to the **/teleop/cmd_vel** topic.

From here **cmd_vel_mux** multiplexes between the messages **/teleop/cmd_vel** and **/move_base/cmd_vel**. The chosen topic is published to **/cmd_vel** and output to the **simple_drive** node which is sent to the drive wheel motor controllers.

## Twist message
Twist message consists of the complementary notions of angular and linear velocity, which together describes the movement of a robot. 

In ROS, messages are custom data structures with typed fields. Nodes send messages to topics to communicate.

The specifics of the message type are described in `.msg` files. Twist refers to the the name of the message type, thus the `Twist.msg` file. The twist messages consists of 2 vectors, each of size 3, `linear` and `angular`

An example of twist message looks like the following:
```
---
linear: 
  x: 0.099132835865
  y: 0.0
  z: 0.0
angular: 
  x: 0.0
  y: 0.0
  z: -0.0
---
```
Note that not all six parameters are going to be used in the rover. Only linear `x` and angular `z` are used, where the former is responsible for forward and backward, and the latter is left and right.

## Joy message
The Joy is the message type that describes which buttons are activated in the joystick.

An example of the joy message:
```
---
header: 
  seq: 10780
  stamp: 
    secs: 1666973065
    nsecs:  63449868
  frame_id: ''
axes: [-0.0, -0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.0]
buttons: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
---
```
Axes are continuous where buttons are discrete values. In joysticks, all the buttons can be classified into one of the two types of controls. You can take a look at them with 
```
rostopic echo /joy
```

## Joystick config file
Joystick-specific config files are in the `config` folder. Note that the config file used when you run `roslaunch` is not automatically adjusted to the joystick model connected to your system. Instead, they are set in the launch files. For example, at the time of writing this, the `turtlesim-drive.launch` uses `f310.config` as defined below:

```
  <!-- Arguments: Modify these as needed -->
  <arg name="joy_config" default="f310" />
  <arg name="joy_dev" default="/dev/input/js0" />
  <arg name="config_filepath" default="$(find teleop_twist_joy)/config/$(arg joy_config).config.yaml" />
```
Note that for each joystick, the button positions in the joy message (shown in the previous section) are different, eg. a logitech joystick might have z button on the 3rd location in the buttons array, but microsoft might have z in the 1st position. This is illustrated in the section 5 of joy package. Note that the positions shown in the joy doc is not necessarily accurate. http://wiki.ros.org/joy 

### Speed control parameters

In `config.yaml` files, set the buttons for shifting up and down. The numbers correspond to the button array in the joy message. Note that because all the launch files set the `joy_config` to `f310`, these parameters are only added in the `f310` config file.
```
shift_up: 3
shift_down: 0
```

In the launch files, set the max speed of the rover in the `max_speed`, which is in m/s. Set is max speed to 2 m/s is a safe starting point. `speed_levels` controls total number of speed levels. The initial speed level is 1. Push the `shift_up` and `shift_down` buttons to change speed level. Note that once the rover stops, the speed level will reset to 1.
```
<node pkg="teleop_twist_joy" name="teleop_twist_joy" type="teleop_node">
    <rosparam command="load" file="$(arg config_filepath)" />
    <param name="max_speed" type="int" value="2"/>
    <param name="speed_levels" type="int" value="3"/>
 </node>
```


## Helpful Resources:
This package is heavily influenced by the official teleop_twist_joy ROS package. Thanks Clearpath. Link: http://wiki.ros.org/teleop_twist_joy

The MUX aspect of this package was reused from the ROS Simple Drive. Thanks Ryerson. http://wiki.ros.org/simple_drive

Joy Node: http://wiki.ros.org/joy/Tutorials/ConfiguringALinuxJoystick

ROS Messages: http://wiki.ros.org/Messages and http://wiki.ros.org/msg

Linear and angular velocities: https://stackoverflow.com/questions/50976281/what-do-x-y-and-z-mean-in-geometry-msgs-twist-message-in-ros

