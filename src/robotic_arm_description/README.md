# Robotic arm Gazebo prototype

Five-joint simulation for ROS 2 Jazzy and Gazebo Harmonic.
This is a prototype, not a calibrated hardware model.

## Build and launch

From the repository root inside the ROS development container:

```bash
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src/robotic_arm_description src/robotic_arm_controls --ignore-src -r -y
colcon build --symlink-install --packages-up-to robotic_arm_description
source install/setup.bash
ros2 launch robotic_arm_description arm_simulation.launch.py
```

The combined launch starts Gazebo, robot_state_publisher, the clock
bridge, both ros2_control controllers, sim_command_bridge, and
integrative_control with simulation_stream_commands enabled.
It does not start the hardware serial router or a joystick driver.
Do not also start separate copies of these simulation nodes.

## Model and frames

Seven visual meshes and seven simplified convex collision meshes:
Base, Hip, Arm, Forearm, Wrist_B, Wrist_A, and EE.

The original STL exports were in millimetres. Processed meshes are
in metres with CAD assembly transforms applied; do not scale them again.

The link chain is:
world -> arm_base_link -> arm_hip_link -> arm_arm_link ->
arm_forearm_link -> arm_wrist_b_link -> arm_wrist_a_link -> arm_ee_link.

The base mounting joint and Forearm-to-Wrist_B joint are fixed.
The other five joints are revolute. Joint origins and axes were derived
from the CAD report. The fixed wrist mount interpretation needs
mechanical review. The current base mounting height is a provisional
1 metre to provide ground clearance.

## Command mapping

Controller order and current provisional input mapping:

| Controller joint | Input channel |
| --- | --- |
| tower_joint | TW |
| shoulder_joint | L1 / EL |
| elbow_joint | L2 / SL |
| wrist_pitch_joint | WP |
| wrist_roll_joint | WR |

The bridge accepts std_msgs/msg/String on /arm_cmd:
S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!

It publishes five velocity values to /arm_velocity_controller/commands.
EE is omitted: the gripper is currently rigid and cannot open or close.
L1/L2 assignment, directions, and actuator-to-joint conversion require
mechanical confirmation. Linear actuator speeds are approximated as
joint angular velocities; linkage kinematics are not modeled.

Default velocity scaling is 0.25 rad/s per unit input.
The bridge sends zero velocity after 0.3 seconds without a valid command.
The explicit stop command is stop;!.

## Joystick input

Simulation streaming uses /joy/controller_1 and ignores controller 2.
Hold RB (button index 5) for arm mode; releasing it sends a stop.
With the current code, axes 3, 4, 7, 0, 1 control TW, L1, L2, WP, WR.
Physical controller mapping has not been tested.
A future physical joystick driver must repeat input, for example at
20 Hz, so steady input does not expire at the bridge.

## Provisional physics

All revolute position limits are +/- pi/2 from the exported CAD pose.
All velocity limits are 0.25 rad/s.
Shoulder and elbow effort limits are 100 N m; the others are 10 N m.
These are simulation assumptions, not measured motor specifications.
Link masses are placeholders and inertias are bounding-box estimates.
Gravity is enabled. Controller-manager command limits are enabled.

Collision hulls fill holes and may create false contacts.
Collision accuracy and clearance throughout the motion range are
not validated. Self-collision behavior has not been validated.

## Validation and remaining work

Observed: all five joints responded to direct velocity commands with
gravity enabled. Simulated joystick messages moved the tower through
the team controls and bridge. Both controllers activated under the
combined launch with command-limit enforcement enabled.

One multi-joint joystick test showed 0.2225 rad shoulder stop drift.
A subsequent isolated shoulder command tracked 0.1 rad/s and held
position after stopping; reverse joystick motion also ended stationary.
The earlier discrepancy remains unresolved, so validation is incomplete.

Still required: gripper articulation, real limits/masses/inertias/torques,
mechanical mapping and direction confirmation, physical controller
testing, motion-range collision checks, and repeatable stop validation.

## Regeneration

Run scripts from the repository root.
scripts/export_meshes.py requires the original mesh archive, CAD report,
NumPy, and SciPy. Keep those source inputs available separately.
scripts/create_description.py regenerates the Xacro, controller YAML,
CMakeLists.txt, and package.xml from config/cad_geometry.json and the
provisional settings in the script. It overwrites those generated files.
Review changes and rebuild after regeneration.
