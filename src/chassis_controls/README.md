# chassis_controls

Drive system for the rover. Provides a `ros2_control` hardware interface that
drives four NEO v1.1 motors through moteus r4.11 controllers in velocity control
over CAN-FD (via the [moteus C++ library](https://github.com/mjbots/moteus)),
plus the operator-side teleop controller.

- Controller / operator guide: [`ControllerREADME.md`](ControllerREADME.md)
- Hardware bring-up test nodes: [`README_testing.md`](README_testing.md)

## Build

```bash
colcon build --packages-select chassis_controls --symlink-install
source install/setup.bash
```

## Launch files
| `rover_gazebo.launch.py` | simulation | Launches the 3D Gazebo Harmonic simulation with differential drive, IMU, 3D LiDAR, and camera sensors |

## Gazebo 3D Simulation

### How to Launch

```bash
ros2 launch chassis_controls rover_gazebo.launch.py

ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.2}}"

| Launch file | Run on | What it does |
| --- | --- | --- |
| `rover.launch.py` | rover / Jetson | Main bringup: `ros2_control` node, diff drive + joint state controllers, `robot_state_publisher`, `twist_mux`, optional joystick and RViz |
| `controller.launch.py` | operator laptop | `joy_node` + the teleop TUI (`controller.py`), publishing to `/cmd_vel_teleop` |
| `joystick.launch.py` | either | `joy_node` + `teleop_twist_joy` using `config/f310.config.yaml` (included by `rover.launch.py`) |
| `drive_rviz.launch.py` | either | RViz with `config/drive.rviz` (included by `rover.launch.py` when `use_rviz:=True`) |

### Bring up the rover

A CAN-FD adapter must be connected **before** launching — the hardware interface
cannot activate without one. With an mjbots fdcanusb nothing else is needed, it
is detected automatically:

```bash
ros2 launch chassis_controls rover.launch.py
```

With a socketcan adapter, bring the interface up in CAN-FD mode first (moteus
uses 1 Mbit/s nominal, 5 Mbit/s data) and set `transport_args` in
`description/urdf/rover.urdf.xacro` to `--socketcan-iface can0`:

```bash
sudo ip link set can0 up type can bitrate 1000000 dbitrate 5000000 fd on
```

`scripts/can_start.sh` brings the bus up as classic CAN, which only suits the
old Talon SRX `drive_test` node.

Arguments for `rover.launch.py`:

| Argument | Default | Meaning |
| --- | --- | --- |
| `use_robot_state_pub` | `True` | Start `robot_state_publisher` |
| `use_rviz` | `False` | Also open RViz |
| `sport_mode` | `true` | Unused since the move to moteus (gains live on the controllers) |
| `use_joystick` | `true` | Start the onboard joystick teleop nodes |

```bash
ros2 launch chassis_controls rover.launch.py use_rviz:=True sport_mode:=false
```

### Drive it

Once `rover.launch.py` is running, use one of:

```bash
# keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/cmd_vel_keyboard
```

```bash
# operator laptop, with the TUI (see ControllerREADME.md)
ros2 launch chassis_controls controller.launch.py
```

Joysticks show up under `/dev/input` on Linux. The Logitech F710 is the
reference pad; it has a "dead man's switch" (**LB**) that must be held for
commands to be sent, with the left stick steering.

> If you are driving from a laptop while `rover.launch.py` is running on the
> Jetson, you must kill the Jetson's phantom `joy_node` first. See
> [`ControllerREADME.md`](ControllerREADME.md#known-issue-phantom-joystick-on-jetson).

## moteus configuration

Set in `description/urdf/rover.urdf.xacro`:

| Property | Default | Meaning |
| --- | --- | --- |
| `FL_id`, `FR_id`, `RR_id`, `RL_id` | `1`, `2`, `3`, `4` | CAN id of each wheel's moteus |
| `gear_ratio` | `100.0` | Motor revolutions per wheel revolution |
| `max_velocity` | `40.0` | Largest velocity sent to a moteus [motor rev/s] |
| `max_torque` | `0.3` | Torque limit sent with every command [Nm] |
| `transport_args` | `auto` | moteus transport arguments, `auto` detects the adapter |

The velocity loop runs on each moteus, so its PID gains are tuned and stored on
the controller (with `tview`), not in this package. The hardware interface
assumes `motor_position.rotor_to_output_ratio` is left at 1 on the moteus and
applies `gear_ratio` itself.

### Command echo

Every command sent to the controllers is published on `/moteus_cmd_echo`
(`sensor_msgs/JointState`), one entry per wheel joint (`q1` FL, `q2` FR, `q3`
RR, `q4` RL):

```bash
ros2 topic echo /moteus_cmd_echo
```

- `position` — always `NaN` (velocity control)
- `velocity` — commanded motor velocity [rev/s], after gear ratio, direction
  and the `max_velocity` limit
- `effort` — torque limit sent with the command [Nm]; `0` on the cycle where a
  stop is sent instead of a velocity

## Prerequisites

The moteus C++ library is fetched by CMake at build time, so the first build
needs internet access.

The rest of this section only applies to the Talon SRX `drive_test` node.

The Phoenix shared libraries in `lib/` must be on the linker path. Add this to
the end of your `~/.bashrc`:

```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/path/to/rover_workspace/src/chassis_controls/lib/arm64
```

Use `arm64` on the Jetson, `arm32` on 32-bit ARM, or `x86-64` on a desktop —
`CMakeLists.txt` picks the matching directory automatically at build time.

### Hardware checklist

1. Check the CAN bus is wired and powered. Red lights on the PDP or Talons mean
   something is wired wrong.
2. Connect the USB→CAN adapter (MicroUSB to USB). On VirtualBox, enable the
   USB2CAN device in the VM; not needed on native Linux.
3. Bring up the bus with `ros2 run chassis_controls can_start.sh`.

## Node graph

<div align="center">
  <img src="docs/chassis_controls_graph.png">
</div>

## Layout

| Path | Contents |
| --- | --- |
| `src/drive_hardware.cpp` | `ros2_control` `SystemInterface` plugin for the moteus controllers |
| `src/drive_test.cpp` | Standalone Talon SRX wheel spin/encoder test node |
| `scripts/controller.py` | Operator teleop TUI |
| `scripts/can_start.sh` | Brings up the CAN interface |
| `config/` | Controller gains, `twist_mux` priorities, joystick mapping, RViz config |
| `description/` | Rover URDF/xacro and meshes |
| `lib/` | Prebuilt CTRE Phoenix shared libraries, per architecture |

## How it works

### Differential drive and PID

- Steering is differential: wheels on one side turn faster than the other, scaled
  by a turning coefficient.
- Each moteus runs the velocity loop that shapes its wheel's response to step commands.
- The diff drive controller is spawned by `controller_manager`.

**Subscribes** `/cmd_vel` — desired linear and angular velocity.
**Publishes** `/odom` (position/velocity estimate) and `/tf` (joint frames).

The controllers need the full robot description — joints (wheels), links
(suspension), and meshes (visuals) — which comes from `config/` and
`description/`.

### Command → robot state

- **Controller manager** — spawns and supervises the PID and diff drive controllers.
- **Joint state broadcaster** — reads all state interfaces and publishes `/joint_states`.
- **Robot state publisher** — subscribes to `/joint_states` and publishes the robot's pose in space for ROS and RViz.
- **`twist_mux`** — arbitrates between teleop, keyboard, and autonomous velocity sources by priority, forwarding the winner to `/diff_cont/cmd_vel_unstamped`.
- **`/tf`** — combines joint states with per-wheel velocity commands to give the pose of each joint and of the rover.

### Power data publisher

Polls PDP status over CAN and publishes battery voltage, per-channel current, and
battery temperature as `general_interfaces/PowerData` (roughly every 10 s) for
monitoring at the base station. Current draw readings are still unstable.

## Resources

- [ROS 2 Control](https://control.ros.org/jazzy/index.html) — how the control nodes operate
- [moteus reference](https://mjbots.github.io/moteus/) — controller configuration, CAN-FD protocol, C++ client
- [CTRE CAN bring-up](https://v5.docs.ctr-electronics.com/en/stable/ch08_BringUpCAN.html) — CAN bus setup and Linux integration
- [CTRE C++ API](https://api.ctr-electronics.com/phoenix/release/cpp/classctre_1_1phoenix_1_1motorcontrol_1_1can_1_1_talon_s_r_x.html) — Phoenix classes used here
- [Intro to URDF](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/Building-a-Visual-Robot-Model-with-URDF-from-Scratch.html)
- [ROS 2 control PID implementation](https://github.com/ros-controls/control_toolbox/blob/ros2-master/src/pid.cpp)
