## Running The Program
1. colcon build
2. source install/setup.bash
3. ros2 launch robotic_arm_controls development_ik.launch.py 

## Dependencies
Before running the Inverse Kinematics code, make sure you have the following dependencies installed on your system:

### Moveit Dependencies
```
sudo apt install ros-humble-moveit
```

### ROS2 Control Related Dependencies**
```
sudo apt-get install ros-humble-joint-trajectory-controller
sudo apt-get install ros-humble-joint-state-broadcaster 
sudo apt-get install ros-humble-controller-manager 
sudo apt-get install ros-humble-joint-state-publisher-gui 
```

### Python Dependencies
```
pip3 install pynput 
pip3 install numpy
```

## RVIZ Configuration
In order to see the robot model in the RVIZ window that is launched, follow these steps:

1. On the bottom left corner click `Add`
2. Select and add `RobotModel` from under `rviz_default_plugins`
3. Under `Global Options` set `Fixed Frame` to `base_footprint`
4. Under `RobotModel` set `Description Topic` to `/robot_description`

## Notes
To run the Inverse Kinematics nodes you must have an Arduino and spacemouse/logitech joystick connected.

* [Test code that simply echoes IK commands back can be found here]()
* [Current Arduino Firmware](https://gitlab.com/uorover/rover_workspace/-/tree/91-circ-robotic-arm-controls/arduino_sketches/rover_robotic_arm/Arm_V2_1_Controls__SPI_?ref_type=heads)
* [The launch files are located here](https://gitlab.com/uorover/rover_workspace/-/tree/91-circ-robotic-arm-controls/src/robotic_arm_controls/launch?ref_type=heads)