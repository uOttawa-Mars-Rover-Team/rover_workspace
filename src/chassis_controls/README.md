# chassis_controls Package

### Node Graph

<div align="center">
  <img src="docs/chassis_controls_graph.png">
</div>

## Purpose

- Describing the methodology of the CAN/ROS interface for the rover.
- Describing "under the hood" of the chassis_control package. 

## Top Level

### Prequisites

-Install all necessary packages (this list is not exhaustive).

```bash
sudo apt update
sudo apt upgrade
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-rviz2 can-utils ros-humble-rqt*
```

- The current library path requires linking via a bash command to properly link the Phoenix libraries in our workspace. Enter the following command at the bottom your bash script with `nano ~/.bashrc`

```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"path/to/rover_workspace/src/chassis_controls/lib/x86-64`
```

### Launching the Nodes

1. The CAN bus has to be brought up before running the launch script, as our ROS controllers can't initialize wihtout a working network.
2. `ros2 run chassis_controls can_start.sh` 
3. `ros2 launch chassis_controls diff_drive.launch.py`

## Under the Hood

### Differential Drive and PID Controllers

- To drive the rover, we use differential drive, which makes wheels on one side turn faster than the other side with a coefficient of turning.
- Our motors are also fit with PID controllers, which manages the response of our wheels to the motor step responses.  
-This controllers are spawned via the `controller_manager`, which is the main manager of both the PID and differential drive controllers.
  
**Subscribes**
- This node describes to the `/cmd_vel` topic, and intepretes expected linear velocity and angular velocity.

**Publishes**
- Publishes to `/odom` , which is an estimate of the robot's position and velocity in free space.
- Publishes to `/tf`, which describes the telemetry and frames of each joint.

**Parameters**
- In spawning the controllers, ROS must know the actual description of our robot, including the joints (wheels), links (suspension), and meshes (visuals).
- These nodes take the full visual and quantitaive description of our rover from the `/config` and  `/description` directories.
  - The `/meshes` folder includes visual desriptions of the rover, via STL files.
  - The `/urdf` folder includes the quantitative description of the joints for our rover, which are critical to the usage of these nodes. 

### Command to Robot State

**Controller Manager**
-Manages the spawning of the PID and differential drive controllers. This manager

**Joint State Broadcaster**
- The broadcaster reads the status of all state interfaces via `/parameter_events`, and publishes them to `/joint_states`.

**Robot State Publisher**
- The robot state publisher is the general interface node of our robot to ROS and RVIZ, and holds the total state of our robot.
-Subscribes to the `/joint_states` topic, and publishes the description of our robot in space. 

**tf**
-This topic holds the general telemetry of our rover in space.
-This node pairs the state of our joints with the velocity command per wheel taken from the PID and diff_drive controllers to output the state and pose of each joint, as well as the velocity and position of the rover.

### Power Data Publisher Node

- This node integrates CTRE's CAN usage into a ROS node, specifically for polling PDP status sequentially. 
- This node is published the battery voltage, current per channel, and batter temperature to be monitored at the base station.
- Current draw is still unstable, will be further explored.

**Publishes**
-This node publishes to the `PowerData` topic, with an array of currents and voltage double. (every 10 seconds as of writing)

## FAQ

### Opening/Driving Robot in RVIZ
1. Under Global Options, change "Fixed Frame" to `/odom`
2. Click "Add", and select RobotModel from `rviz_default_plugins` directory.
3. Under RobotModel, change "Description Topic" to `/robot_description`.
4. To drive the rover around in RVIZ, launch a node to publish to `/cmd_vel`. 
- `ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped`

### Hardware Setup
1. First, ensure the CAN bus is connected properly and the power is on. If you see red lights on the PDP or Talons, something is wired wrong. 
2. Connect the USB --> CAN to your computer via MicroUSB to USB, and enable the USB2CAN in VirtualBox. (not needed for native Linux).
3. Bring up the CAN bus using above launch command.

### Helpful Links
[ROS2 Controls](https://control.ros.org/humble/index.html)
- Gives a thorough description on the operation of control nodes.
[CTRE Bring-Up](https://v5.docs.ctr-electronics.com/en/stable/ch08_BringUpCAN.html)
- Describes methodology in setting up CAN bus and Linux integration.
[CTRE C++ Documentation](https://api.ctr-electronics.com/phoenix/release/cpp/classctre_1_1phoenix_1_1motorcontrol_1_1can_1_1_talon_s_r_x.html)
- Documentation of CTRE C++ library for all functions and classes used in pkg.
[Intro to URDF](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html)
- Gives a simple example of simulating a robot in URDF using RVIZ.
[ROS2 Control PID Documentation](https://github.com/ros-controls/control_toolbox/blob/ros2-master/src/pid.cpp)
- Provides documentation for the ROS2 control toolbox implemented PID controller.

