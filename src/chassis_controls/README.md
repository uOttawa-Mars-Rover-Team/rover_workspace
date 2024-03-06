# chassis_controls Package

### Node Graph

<div align="center">
  <img src="docs/chassis_controls_graph.png">
</div>

## Purpose

- Describing the methodology of the CAN/ROS interface for the rover.

## Starting the CAN BUS

### Launch

1. The can bus has to be brought up before running the drive_control and power_publisher. Run the following commands (or create a bash alias ;))
2. `ros2 run chassis_controls can_start.sh` --> `ros2 launch chassis_controls chassis.launch.py`

### Non-Launch Method

1. First, ensure the CAN bus is connected properly and the power is on. If you see red lights on the PDP or Talons, something is wired wrong. 
2. Connect the USB --> CAN to your computer via MicroUSB to USB, and enable the USB2CAN in VirtualBox. (not needed for native Linux).
3. Bring up the CAN bus using `./can_start.sh`, which will bring up our CANbus as "can0".
4. Start the drive motor control by running `ros2 run  chassis_controls drive_control`
5. Start the power publisher by running `ros2 run chassis_controls power_data_publisher`

## Drive Motor Node

1. The drive motor node is a subscriber/publisher, which subscribes to the input data from the teleop_joy node (aka. joystick), and sets the motors to that input.
2. This node will also publish feedback from the motors at a given rate, which will be used for feedback purposes to know our motor speed and flags.
3. Current and voltage draw from each motor can also be sensed, as well as sticky faults. 

## Power Data Publisher

1. The power data publisher publishes the battery health of the rover.
2. In the future, research will be done to try to use the complex current draw array, which is currently unusable.

