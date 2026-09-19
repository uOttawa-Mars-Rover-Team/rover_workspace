# gps_node

GPS and IMU publishing for the rover — the nodes that report where the rover is
and how it is oriented.

The package currently wraps the [`ublox_dgnss`](https://github.com/aussierobots/ublox_dgnss)
driver for our u-blox RTK receiver, and ships dummy publishers for testing
without hardware.

## Build

```bash
colcon build --packages-select gps_node
source install/setup.bash
```

## Launch files

Both launch files just include the matching `ublox_dgnss` launch file, so the
`ublox_dgnss` package must be installed and the receiver plugged in over USB.

| Launch file | Run on | What it does |
| --- | --- | --- |
| `rover.launch.py` | rover / Jetson | Starts the u-blox receiver in **rover** (moving base) mode |
| `base.launch.py` | base station | Starts the u-blox receiver in **base** (fixed RTK reference) mode |

```bash
# on the rover
ros2 launch gps_node rover.launch.py

# on the base station
ros2 launch gps_node base.launch.py
```

## Nodes

| Executable | Purpose |
| --- | --- |
| `gps_dummy_node` | Publishes fake `general_interfaces/GPS` data for testing the dashboard / navigation without hardware |
| `imu_dummy_node` | Publishes fake `general_interfaces/IMU` data for the same reason |

```bash
ros2 run gps_node gps_dummy_node
ros2 run gps_node imu_dummy_node
```

> Note: `setup.py` also declares a `gps_node` executable pointing at
> `gps_node/gps_node.py`, but that file is not in the repo (it was the old
> Arduino serial reader). Building is fine, but `ros2 run gps_node gps_node`
> will fail until the file is restored or the entry point is removed.

## Checking the data

```bash
ros2 topic list
ros2 topic echo /fix          # or whatever topic the driver/dummy publishes
ros2 topic hz /fix
```

## Coordinate format

Older Arduino-sourced data reported `latitude`/`longitude` in degrees and
decimal minutes (`DDMM.MMMM` — first two characters are degrees, the rest are
minutes) rather than decimal degrees. If you are reading raw NMEA, convert
before feeding it to navigation. See
[Adafruit's explanation](https://learn.adafruit.com/adafruit-ultimate-gps/direct-computer-wiring/).

## Resources

- [GPS wiki page](https://gitlab.com/uorover/rover_workspace/-/wikis/Research/GPS-for-Rover)
- [Adafruit Ultimate GPS](https://learn.adafruit.com/adafruit-ultimate-gps/)
- [SparkFun LSM9DS1 IMU](https://learn.sparkfun.com/tutorials/lsm9ds1-breakout-hookup-guide/all)
