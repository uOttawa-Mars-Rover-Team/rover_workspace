# robotic_arm_controls

Teleoperation and inverse-kinematics control for the rover's robotic arm.
Gamepad/spacemouse input is turned into joint commands, which are serialised and
sent over USB serial to the arm's microcontroller (see
[`rover_embedded_shield`](../../rover_embedded_shield)).

## Build

```bash
colcon build --packages-select robotic_arm_controls
source install/setup.bash
```

## Launch files

Launch files are named `<where-it-runs>_<control-mode>.launch.py`:

- `development_*` — on a dev machine / in simulation
- `basestation_*` — on the operator laptop
- `roverpc_*` — on the rover's onboard computer (Jetson)
- `manual` — direct joint control; `ik_servo` — MoveIt Servo / IK control

| Launch file | Runs |
| --- | --- |
| `integrative_ctrl.launch.py` | **Recommended starting point.** Two gamepads + combined drive/arm control node + serial router |
| `development_manual.launch.py` | Two joy nodes, keyboard node, IK joy node, serial router |
| `development_ik_servo.launch.py` | Joy + keyboard + IK joy nodes, includes `arm_controls/arm_servo.launch.py` |
| `development_ik_gui.launch.py` | Same as above but includes `arm_controls/arm_gui.launch.py` |
| `basestation_manual.launch.py` | Operator-side joy + keyboard + IK joy nodes (no serial router) |
| `basestation_ik_servo.launch.py` | Spacemouse + keyboard + IK joy nodes + RViz with MoveIt config |
| `roverpc_manual.launch.py` | Just the serial router (`m_router`) on the rover |
| `roverpc_ik_servo.launch.py` | Just `arm_controls/arm_servo.launch.py` on the rover |

```bash
ros2 launch robotic_arm_controls integrative_ctrl.launch.py
```

> **Heads up:** the `*_ik_servo` and `*_ik_gui` launch files include launch files
> from an `arm_controls` package that is **not present in `src/`**. They will
> fail with a `PackageNotFoundError` until that package is added back. The
> `manual` and `integrative_ctrl` launch files work without it.

### Typical split-machine setup

```bash
# on the rover
ros2 launch robotic_arm_controls roverpc_manual.launch.py

# on the operator laptop
ros2 launch robotic_arm_controls basestation_manual.launch.py
```

## Nodes

| Executable | Purpose |
| --- | --- |
| `integrative_control` | Single gamepad node for **both** driving and the arm. Hold **LB** for drive mode (`/cmd_vel_teleop`), **RB** for arm mode (`/arm_cmd`) |
| `ik_joy_controls` | Maps gamepad/spacemouse axes to arm motion (manual or IK mode) |
| `ik_keyboard_controls` | Keyboard control / velocity override |
| `m_router` | Serial router — forwards `/arm_cmd` strings to the microcontroller |
| `arm_gui_term` | Terminal GUI for monitoring the arm |
| `template_pub_sub` | Skeleton publisher/subscriber to copy when adding a node |

```bash
ros2 run robotic_arm_controls arm_gui_term
```

## Common parameters

Set these with `--ros-args -p name:=value`, or edit the launch file.

| Parameter | Node | Meaning |
| --- | --- | --- |
| `mode` | `ik_joy_controls`, `ik_keyboard_controls` | `"M"` for manual joint control |
| `deadzone` | `ik_joy_controls` | Stick deadzone (default `0.4` in launch files) |
| `pub_rate` | `ik_joy_controls` | Publish rate in Hz (default `20.0`) |
| `dirTW` / `dirL1` / `dirL2` / `dirWP` / `dirWR` | joy nodes | Per-joint direction; set to `-1` to invert |
| `serial_dev` | `m_router` | Serial port, e.g. `/dev/ttyACM0` |
| `baudrate` | `m_router` | Serial baud rate (`9600`) |
| `read_enable` | `m_router` | Read replies back from the microcontroller |

## Topics

| Topic | Type | Direction |
| --- | --- | --- |
| `/joy/...` | `sensor_msgs/Joy` | in — raw gamepad input (remapped per device) |
| `/arm_cmd` | `std_msgs/String` | out — arm command string, consumed by `m_router` |
| `/cmd_vel_teleop` | `geometry_msgs/Twist` | out — drive commands from `integrative_control` |

Arm command string format:

```text
S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!
```

## Troubleshooting

- **No joystick input** — check `ls /dev/input/js*`, and that the `device_id` /
  `dev` parameter in the launch file matches your controller.
- **`Permission denied` on `/dev/ttyACM0`** — `sudo usermod -aG dialout $USER`,
  then log out and back in.
- **Wrong joint direction** — flip the matching `dir*` parameter to `-1`.

## TODO

## Simulation command bridge (model integration pending)

`sim_command_bridge` translates the existing `/arm_cmd` `std_msgs/String`
velocity frames to `/arm_velocity_controller/commands`
(`std_msgs/Float64MultiArray`). It does not start the serial router or connect
to the physical arm. This bridge alone does **not** spawn an arm in Gazebo.
The arm meshes, joint frames, limits, inertias, controller YAML and Gazebo
launch remain to be integrated.

The receiving `velocity_controllers/JointGroupVelocityController` must list
its six joints in the exact wire order: **TW, EL, SL, WP, WR, EE**. This order
is a command ordering, not a declaration of the arm's physical link tree.
The EE joint type and its conversion require confirmation from CAD/mechanical
information. For revolute joints the output units are radians per second;
for prismatic joints they are metres per second.

```bash
ros2 run robotic_arm_controls sim_command_bridge
```

In a second sourced terminal, check the output without a simulator:

```bash
ros2 topic echo /arm_velocity_controller/commands
```

In a third sourced terminal, send a single test command:

```bash
ros2 topic pub --once /arm_cmd std_msgs/msg/String '{data: "S;1;0;0;0;0;0;!"}'
```

Expected: `[0.25, 0, 0, 0, 0, 0]`, then all zeros after 0.3 seconds.
The bridge publishes at 50 Hz. `velocity_scales` defaults to six **provisional**
values of 0.25 output units per second at full input. Input multipliers are
clamped to [-1, 1]. Tune and verify each scale before judging simulated speed.
`command_timeout` is configurable; the watchdog uses monotonic wall time.
Malformed frames and unsupported commands stop the simulated command, including
`set0;!`, which does not teleport or recalibrate the simulated model.

Only run one command source during this test. Do not run `m_router` for
simulation. If the bridge process itself dies, its watchdog cannot send zeros;
the receiving controller requires its own stop strategy for that case.

Reference: https://control.ros.org/jazzy/doc/ros2_controllers/velocity_controllers/doc/userdoc.html

- Restore or remove the dependency on the missing `arm_controls` package.
- Document the IK implementation under `robotic_arm_controls/InverseKinematics/`.
