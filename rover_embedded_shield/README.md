# rover_embedded_shield

Firmware for the rover's Arduino Mega 2560 shield. It receives command strings
over USB serial from the ROS side (see
[`robotic_arm_controls`](../src/robotic_arm_controls) → `m_router`) and drives
servos, steppers, linear actuators, LEDs, and reads encoders.

This is a [PlatformIO](https://platformio.org/) project, **not** a ROS package —
`colcon build` ignores it.

## Setup

Install the PlatformIO CLI (or the VS Code PlatformIO extension):

```bash
pip install platformio
```

## Build and upload

The project has several environments, one per application. Pick the one matching
the board you are flashing:

| Environment | Build flag | Application |
| --- | --- | --- |
| `AppRA` | `-D APP_RA` | Robotic arm — joint control, end effector, LEDs |
| `AppGNC` | `-D APP_GNC` | Guidance/navigation shield |
| `AppGNCDebug` | `-D APP_GNC -D APP_GNC_DEBUG` | Same as `AppGNC` with debug output |

```bash
cd rover_embedded_shield

# compile only
pio run -e AppRA

# compile and flash the connected board
pio run -e AppRA -t upload

# watch the serial output
pio device monitor -b 9600
```

If the upload cannot find the board, pass the port explicitly:
`pio run -e AppRA -t upload --upload-port /dev/ttyACM0`. On Linux you may need
to be in the `dialout` group: `sudo usermod -aG dialout $USER`, then log out and
back in.

## Layout

| Path | Contents |
| --- | --- |
| `src/main.cpp` | Entry point; dispatches to the app selected by the build flag |
| `src/apps/` | Top-level applications (`AppRA`, `AppGNC`, `AppMorseServo`) |
| `src/comms/` | `CommSerial` — serial command parsing |
| `src/drivers/` | Low-level hardware drivers (servo, stepper, encoder, linear actuator, LED) |
| `src/tasks/` | Cooperative tasks (joint control, end effector, LED, servo, button) |
| `include/` | Headers for the above |
| `lib/Servo/` | Vendored Servo library — **locally modified**, do not replace with the upstream version |

## Dependencies

Declared in `platformio.ini` and fetched automatically:

- `waspinator/AccelStepper`
- `paulstoffregen/TimerThree`
- `pololu/JrkG2`

`Servo` is deliberately **not** fetched — the copy in `lib/Servo/` has local
changes that a fetched version would overwrite.

## Serial protocol

Commands are newline-free, delimited strings. Two forms are in use:

```text
S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!    arm joint velocities
SV;<A|B>;<x>;<y>!                    servo pan/tilt
```

The `m_router` node on the ROS side forwards `/arm_cmd` (`std_msgs/String`)
straight through at 9600 baud.
