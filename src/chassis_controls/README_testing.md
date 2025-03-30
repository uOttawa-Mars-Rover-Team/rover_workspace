# Testing Nodes

## `drive_control` Node

- Spins a wheel at a specified output level (either PWM or Velocity)

### Usage

```bash
# Spin the RR wheel at 0.1 PWM
ros2 run chassis_controls drive_control RR 0.1
# (Alternative) Spin the RR wheel at 0.1 PWM
ros2 run chassis_controls drive_control RR 0.1 0

# Spin the RR wheel at 1 Velocity
ros2 run chassis_controls drive_control RR 1 1
```

## `drive_test` Node

- Spins a wheel at a specified output level (either PWM or Velocity). Approximately each second, print out the number of rotations per second the wheel is spinning at
- Spin a specific wheel by its name: RR, RL, FR, FL. Or spin all wheels with: ALL.
- Logging and time checking makes this slightly slower (real time) than `drive_control`
- When using PWM control, the main input parameter passed in is the PWM level, ranging from -1 to 1. When using Velocity control, the main input parameter passed in is the number of encoder ticks per 100ms to spin at
- When using Velocity control, optionally pass in FPID gains to the motor controllers as extra positional arguments

### Usage

```bash
# Spin the RR wheel at 0.1 PWM
ros2 run chassis_controls drive_test RR 0.1
# (Alternative) Spin the RR wheel at 0.1 PWM
ros2 run chassis_controls drive_test RR 0.1 0

# Spin the RR wheel at 1 encoder tick per 100ms using Velocity control
ros2 run chassis_controls drive_test RR 1 1
# Spin the RR wheel at 409.6 encoder ticks per 100ms using Velocity control, setting FPID gains as 0.0 (F), 1.6 (P), 0.016 (I) and 160 (D)
ros2 run chassis_controls drive_test RR 409.6 1 0.0 1.6 0.016 160
```
