# drive_controls package

This package is meant to house code related to the development of the rover's drive system.

The code in this package was initially migrated from our old `teleop_twist_joy-melodic-devel` package (which was a copy of the external `teleop_twist_joy` package with added code) that was meant for ROS Melodic.

## TODO

- test the code to ensure it works as expected (the migration to ROS2 might have left bugs)
- update this README with a description of the nodes, topics, launch files, etc.

### Launch Files

- Look into reusing `base_station_pc.launch` for the majority of `turtlesim_drive.launch.py`, including remaps where necessary
