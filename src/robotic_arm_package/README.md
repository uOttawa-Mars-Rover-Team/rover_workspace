# ROS Package: robotic\_arm\_package

## Info

__Messages:__ std_msgs.msg, sensor_msgs.msg  

__Scripts:__ arm\_joystick\_controller.py, arm\_control.py

__Maintainers:__ Justin Zhang

__Prerequisites & Hardware Setup:__ arm\_control node must connect to an Arduino running the RobotArmControls.ino sketch in the arduino_sketches folder (see link 1. at the bottom). Moreover, arm\_joystick\_controller node subscribes to /joy messages, so it is advised to start a joy node after setting up the joystick (see link 2. at the bottom); optionally, if no joystick is available, one can manually publish /joy messages using 'rostopic pub /joy sensor_msgs/Joy ' then tab after the space.

## Description

The arm\_control node is a ROS node that runs an /arm_control subscriber & writes via serial to the arduino.   

The arm\_joystick\_controller node is a ROS node that subscribes to the /joy topic and publishes the aforementioned /arm_control messages.   

/arm_control message is of type String (std_msgs.msg). This message can either be "stop" or is of the form "X;Y;Z", where X (part): {tower_rotation, arm_angle, forearm_angle, wrist_roll, wrist_pitch, claw_angle}, Y (direction): 1.0 to -1.0 & Z (velocity): 0.0 to 2.0.

The arduino receives via serial, messages from the arm\_control node. These messages can be the "stop;!" command or similar to the above, of the form "A;B;C;!", where A (part): {TW, L1, L2, WR, WP, EE}, B (direction): {1,-1} & C (velocity): 0-255 for the linear actuators (L1 & L2) & for the motors 0-1000.

## Helpful Resources:

1. RobotArmControls.ino: https://gitlab.com/uorover/rover_workspace/-/blob/robot-arm-main/arduino_sketches/rover_robotic_arm/RobotArmControls/RobotArmControls.ino   
2. Joystick setup: https://gitlab.com/uorover/rover_workspace/-/wikis/How-To/Joystick-Setup-for-ROS   

