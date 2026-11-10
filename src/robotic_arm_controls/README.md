# robotic_arm_controls

Teleoperation for the rover's robotic arm. Controller input is turned into
joint commands, which are serialised and sent over USB serial to the arm's
microcontroller (see [`rover_embedded_shield`](../../rover_embedded_shield)).

Joint-space control is the whole of it right now. There is an inverse-
kinematics path in the code, but nothing in this workspace listens to it —
see [Known gaps](#known-gaps).

## Layout

```
arm_nodes/      the ROS nodes (this is the importable Python module)
launch/         the three launch files
scratch/        standalone experiments; not nodes, not installed
test/           ament linter stubs
```

`arm_nodes/` is deliberately not called `robotic_arm_controls/`. ROS 2's
default `ament_python` layout names that folder after the package, which gives
you `robotic_arm_controls/robotic_arm_controls/` and a folder whose name tells
you nothing about what is in it. The ROS package is still
`robotic_arm_controls` — that comes from `package.xml`, not from the folder —
so `ros2 run` and `ros2 launch` are unaffected. Python imports inside the
package use `arm_nodes`:

```python
from arm_nodes import arm_translation as proto
```

## Build

```bash
colcon build --packages-select robotic_arm_controls
source install/setup.bash
```

## Launch files

Four, split by what you are doing and where you are sitting.

**Arm only** — flight stick + Xbox pad:

| Launch file | Where you run it | What it starts |
| --- | --- | --- |
| `manual.launch.py` | At the rover, controllers plugged into the Jetson | Controllers + keyboard + arm control + serial router |
| `basestation_arm.launch.py` | Operator laptop | Controllers + keyboard + arm control |
| `rover_arm.launch.py` | On the rover, driving from the base station | Serial router only |

**Drive and arm together** — Xbox pads only:

| Launch file | Where you run it | What it starts |
| --- | --- | --- |
| `integrative.launch.py` | At the rover, pads plugged into the Jetson | One or two pads + keyboard + combined drive/arm control + serial router |

**All on one machine** — controllers plugged straight into the Jetson:

```bash
ros2 launch robotic_arm_controls manual.launch.py
```

**Split across two machines** — run one on each:

```bash
# on the rover
ros2 launch robotic_arm_controls rover_arm.launch.py

# on the operator laptop
ros2 launch robotic_arm_controls basestation_arm.launch.py
```

`manual.launch.py` is exactly the other two put together, so never run it
alongside `rover_arm.launch.py` — you would end up with two serial routers
fighting over the same port. Same goes for `integrative.launch.py`: it is a
complete setup on its own and publishes to `/arm_cmd` just like `manual` does,
so run one or the other.

**Drive and the arm from one pad** — hold **LB** for drive, **RB** for the
arm, neither or both for a safe stop:

```bash
ros2 launch robotic_arm_controls integrative.launch.py                 # two pads
ros2 launch robotic_arm_controls integrative.launch.py controllers:=1  # one pad
```

With two pads each is handled independently, so one person can drive while
another works the arm.

### Options

Every launch file takes arguments in the usual `name:=value` form.

| Argument | Files | Default | Meaning |
| --- | --- | --- | --- |
| `mode` | `manual`, `basestation_arm` | `M` | `M` = manual joint control; `I` = IK, which nothing currently consumes |
| `controllers` | `integrative` | `2` | How many Xbox pads are plugged in (`1` or `2`) |
| `serial_dev` | `manual`, `integrative`, `rover_arm` | `/dev/ttyACM0` | Serial port the arm microcontroller is on |
| `joy_a_id` / `joy_b_id` | all but `rover_arm` | `0` / `1` | Device index of each controller |
| `joy_a_name` / `joy_b_name` | all but `rover_arm` | *(empty)* | Exact device name; overrides the index when set |

Joint directions and the stick deadband are not launch arguments. They change
only when the arm is rebuilt or rewired, so they live in a clearly marked block
at the top of each launch file — edit them there.

> Note: `manual.launch.py`, `basestation_arm.launch.py` and
> `integrative.launch.py` do not all agree on `dirTW` / `dirL2`; they were
> written at different times against the same arm. Whichever one turns a joint
> the wrong way is the wrong one — flip it in that file.

## Controllers

The arm is flown with a **Turtle Beach VelocityOne Flightstick** for the tower
and the two links, and an **Xbox pad** for the wrist and the peripherals.

Two joy nodes are started, but **it does not matter which controller ends up on
which one.** `joy_controls` works out which controller sent a message from the
message itself — the button count is a property of the hardware — rather than
trusting the device index. Plug them in in any order, in either port, and
reboot as often as you like.

| Buttons | Device | Drives |
| --- | --- | --- |
| 24 | Turtle Beach VelocityOne Flightstick | TW, L1, L2, speed dial, gripper, servo |
| 11 | Xbox pad | WP, WR, camera servo, stepper toggles |
| 12 | Logitech Extreme 3D Pro | TW, L1, L2, speed dial — the older stick, still supported |
| 2 | SpaceMouse | Gripper (IK mode only) |

A controller whose button count is not in that table falls back to whatever its
topic normally carries — `/joy/arm_stick` is read as a VelocityOne,
`/joy/arm_pad` as an Xbox pad — and says so in the log. Unfamiliar hardware
still works, as long as it is on the right topic.

Watch the startup log to see what it decided:

```text
[joy_controls]: /joy/arm_stick: 24 buttons -> velocityone
[joy_controls]: /joy/arm_pad: 11 buttons -> gamepad
```

**If two controllers report the same button count** they cannot be told apart,
and the node logs an error saying so. That is the one case where you have to
pin them by name:

```bash
ros2 run joy joy_enumerate_devices      # prints each index and its exact name
ros2 launch robotic_arm_controls manual.launch.py \
    joy_a_name:="VelocityOne Flightstick"
```

### Nothing moves until you move it

Every axis and button starts out neutral and is ignored until it has been seen
to change. `joy_node` reports the state of every input the moment it opens a
device, and an untouched trigger or throttle often reads a hard `-1.0` or
`+1.0` rather than `0.0` — which used to make the arm take off the instant the
launch file came up and only settle once someone wiggled the sticks.

Two consequences worth knowing:

- The speed dial sits at its default (`max_vel` 0.7) until you first turn it,
  whatever position it is physically in.
- A button held down as the node starts does nothing until you let go of it.

`joy_controls` also sends one all-stop command a second after it starts, so
the microcontroller is not left repeating whatever it was doing before.

## Nodes

| Executable | Purpose |
| --- | --- |
| `joy_controls` | Maps controller axes to arm motion. The main node |
| `keyboard_controls` | Keyboard speed trim and toggles |
| `m_router` | Serial router — forwards `/arm_cmd` strings to the microcontroller |
| `integrative_control` | Single gamepad for **both** driving and the arm. Hold **LB** to drive, **RB** for the arm |
| `arm_gui_term` | Terminal GUI for monitoring the arm |
| `template_pub_sub` | Skeleton publisher/subscriber to copy when adding a node |

```bash
ros2 run robotic_arm_controls arm_gui_term
```

## Controls

### VelocityOne Flightstick (24 buttons)

| Input | Action |
| --- | --- |
| Axis 2 | TW — tower |
| Axis 4 | L1 — link 1 |
| Axis 1 | L2 — link 2 |
| Axis 5 | Global speed, `0.4` to `1.0` |
| Button 2 | Toggle firmware verbose output |
| Button 3 | Reset all encoders |
| Button 15 / 17 | Gripper open / close |
| Button 16 | Servo: tap, hold and release each send their own command |

Nothing on the stick is bound to the tower-only speed trim — use the keyboard's
`{` and `}` for that. If you want it on a stick button, say which one.

### Xbox pad (11 buttons)

| Input | Action |
| --- | --- |
| Left stick Y / X | WP — wrist pitch / WR — wrist roll |
| Left trigger | Shoulder camera servo down |
| Button 4 (LB) | Shoulder camera servo up |
| A / B / X / Y | Toggle stepper 4 (EE) / 3 (WR) / 1 (TW) / 2 (WP) |

### Logitech Extreme 3D Pro (12 buttons)

The older stick. Still supported, not what the arm is flown with now.

| Input | Action |
| --- | --- |
| Stick twist / fore-aft / hat vertical | TW / L1 / L2 |
| Throttle | Global speed |
| Button 4 / 5 | Tower-only speed trim, up / down |
| Button 11 | Toggle firmware verbose output |

### Xbox pad, in `integrative.launch.py`

The pad does both jobs, with the bumpers acting like shift keys.

| Input | Action |
| --- | --- |
| Hold **LB** | Drive mode — left stick steers, hold **Y** for turbo |
| Hold **RB** | Arm mode — right stick TW/L1, D-pad L2, left stick WP/WR |
| **A** / **B** in arm mode | Gripper close / open |
| Neither or both bumpers | Nothing published — safe stop |

### Keyboard (`keyboard_controls`)

| Key | Action |
| --- | --- |
| `.` / `,` | Global speed up / down |
| `}` / `{` | Tower-only speed up / down |
| `!` `@` `#` `$` | Toggle steppers 1–4 (TW, WP, WR, EE) |
| `1` | Toggle emergency stop |
| `0` | Zero the encoders |
| `O` / `P` | Shoulder camera servo up / down |
| `V` | Toggle firmware verbose output |
| `s` | Call the `servo_node/start_servo` service (IK mode) |

## Parameters

Set these with `--ros-args -p name:=value`, or edit the launch file.

| Parameter | Node | Meaning |
| --- | --- | --- |
| `mode` | `joy_controls`, `keyboard_controls` | `"M"` manual joint control, `"I"` IK |
| `deadband` | `joy_controls` | Stick deadband (`0.4` in the launch files) |
| `dirTW` / `dirL1` / `dirL2` / `dirWP` / `dirWR` | `joy_controls`, `integrative_control` | Per-joint direction; `-1` inverts |
| `scale_linear` / `scale_angular` / `turbo_mult` | `integrative_control` | Drive speed scaling |
| `serial_dev` | `m_router` | Serial port, e.g. `/dev/ttyACM0` |
| `baudrate` | `m_router` | Serial baud rate (`9600`) |
| `read_enable` | `m_router` | Log replies from the microcontroller |
| `timeout_delay` | `m_router` | Serial reconnect interval in seconds |

## Topics

| Topic | Type | Direction |
| --- | --- | --- |
| `/joy/arm_stick`, `/joy/arm_pad` | `sensor_msgs/Joy` | in — controller input; `/joy/arm_cmd_logitech` and `/joy/arm_cmd_xbox` still work as the old names |
| `/joy/controller_1`, `/joy/controller_2` | `sensor_msgs/Joy` | in — pads, `integrative_control` only |
| `/keyboard/arm_vel`, `/keyboard/arm_vel_tw` | `std_msgs/Float32` | in — speed trim from the keyboard node |
| `/arm_cmd` | `std_msgs/String` | out — arm command string, consumed by `m_router` |
| `/cmd_vel_teleop` | `geometry_msgs/Twist` | out — drive commands from `integrative_control` |
| `/servo_node/delta_twist_cmds` | `geometry_msgs/TwistStamped` | out — IK mode only |
| `/gripper_control/gripper_velocities` | `general_interfaces/GripperControl` | out — IK mode only |

Arm command string format:

```text
S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!
```

Each field is a velocity in `[-1.0, 1.0]`. Other strings on `/arm_cmd` carry
their own prefix — `SV;C;<dir>;!` for the camera servo, `RA;...!` for firmware
commands, `v;!` for the verbose toggle.

## Troubleshooting

- **No joystick input** — check `ls /dev/input/js*`, then
  `ros2 run joy joy_enumerate_devices`. If a controller is missing there, it is
  a driver or permissions problem, not a launch file one.
- **A joint moves the wrong way** — flip the matching `dir*` entry at the top
  of the launch file to `-1`.
- **A joint does nothing** — check `ros2 topic echo /arm_cmd`. If the field
  stays at `0.0`, that axis has not been "woken up" yet; move it through its
  full range once.
- **`Permission denied` on `/dev/ttyACM0`** — `sudo usermod -aG dialout $USER`,
  then log out and back in.
- **The arm stops responding after a while** — `m_router` reconnects silently
  on serial errors; watch its log for `Connection Error`.

## Known gaps

- IK mode (`mode:=I`) publishes for MoveIt Servo, but the MoveIt config, the
  servo launch files and the RViz config lived in an `arm_controls` package
  that is not in `src/`. Until that comes back, nothing is listening.
- **The two input nodes speak different dialects at the firmware.**
  `arm_translation.py` documents the `Arm_V2_2` grammar as `svu;!`/`svd;!`/
  `svs;!`, `stepper1;!` and `set0;!`, which is what `keyboard_controls` sends.
  `joy_controls` sends `SV;C;1;!`, `RA;stepper1!` and `RA;SET0!` instead.
  Both predate this rewrite and both are preserved as they were — but at most
  one of them matches whatever is flashed. Worth resolving against the actual
  firmware, and `arm_translation.py` is the right place to put the answer.
