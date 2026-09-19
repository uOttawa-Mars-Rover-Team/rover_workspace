# Hardware Test Nodes

Standalone nodes for bringing up and checking the drive hardware, without
running the full `ros2_control` stack. Bring up the CAN bus first:

```bash
ros2 run chassis_controls can_start.sh
```

## `drive_test`

Spins a wheel (or all wheels) at a given output level, in either PWM or Velocity
mode, and prints the measured rotations per second roughly once a second.

- Wheel names: `RR`, `RL`, `FR`, `FL`, or `ALL` for every wheel.
- Control mode is the second positional argument: `0` = PWM (default), `1` = Velocity.
- In **PWM** mode the output level ranges from `-1` to `1`.
- In **Velocity** mode the output level is encoder ticks per 100 ms, and you may
  optionally pass FPID gains as extra positional arguments.

### Usage

```bash
# Spin the RR wheel at 0.1 PWM
ros2 run chassis_controls drive_test RR 0.1
# Same thing, with the mode given explicitly
ros2 run chassis_controls drive_test RR 0.1 0

# Spin the RR wheel at 1 encoder tick per 100ms using Velocity control
ros2 run chassis_controls drive_test RR 1 1

# Spin the RR wheel at 409.6 ticks per 100ms, setting FPID gains
# F=0.0, P=1.6, I=0.016, D=160
ros2 run chassis_controls drive_test RR 409.6 1 0.0 1.6 0.016 160
```

> A `drive_control` node (the same thing without the per-second logging, so
> slightly faster in real time) is referenced in older notes but is not currently
> built by `CMakeLists.txt`. Use `drive_test`.
