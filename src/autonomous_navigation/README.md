# autonomous_navigation Package

## Instructions for rviz demo

    cd ws and build
    ros2 launch autonomous_navigation launch.py
    bottom right corner -> add -> RobotModel
    set Fixed Frame -> base_link
    set Description Topic -> /robot_description

It should automatically open the joint state publisher also

## Instructions for gazebo demo (WIP)

Source: https://youtu.be/IjFcr5r0nMs

```bash
  ros2 launch autonomous_navigation drive_sim.launch.py
```

- Control option 1: In a seperate terminal, run teleop_twist_keyboard (with remappings)

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
```

- Control option 2: In seperate terminals, run the joy and teleop control nodes

```bash
ros2 run joy joy_node
ros2 run teleop_twist_joy teleop_node
```

## Instructions for autonav demo (WIP)

- Launch `waypoints.launch.py`

```bash
ros2 launch autonomous_navigation waypoints.launch.py
```

- Use Rviz to set a target pose by clicking on the `Nav2 Goal` button in the middle of the top navbar. The robot should autonomously navigate to the specified pose (to the best of its ability) in Gazebo
