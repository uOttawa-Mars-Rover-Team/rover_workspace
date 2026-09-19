# autonomous_navigation

Simulation and autonomous navigation for the rover: URDF/Gazebo models, Nav2
bringup, and EKF sensor fusion (`robot_localization`) for GPS + IMU + odometry.

## Build

```bash
colcon build --packages-select autonomous_navigation
source install/setup.bash
```

## Launch files

| Launch file | What it does |
| --- | --- |
| `launch.py` | RViz + `robot_state_publisher` + `joint_state_publisher` — just view the robot model, no simulation |
| `drive_sim.launch.py` | Gazebo world (`smalltown.world`) with the rover, `ros2_control` diff drive, and joystick teleop |
| `waypoints.launch.py` | Gazebo (`obstacles.world`) + Nav2 + RViz — full autonomous navigation demo |
| `navigation.launch.py` | Nav2 planner/controller/behaviour nodes. **Include-only** — not useful on its own |
| `localization_launch.py` | Nav2 `map_server` + `amcl`. **Include-only** |
| `gps_navsat.launch.py` | Dual-EKF + `navsat_transform` for GPS-based localisation on the real rover |

### View the robot model in RViz

```bash
ros2 launch autonomous_navigation launch.py
```

RViz and the joint state publisher open automatically. If the model does not
appear: **Add** (bottom left) → **RobotModel**, set *Fixed Frame* to `base_link`
and *Description Topic* to `/robot_description`.

Useful arguments: `use_rviz`, `use_robot_state_pub`, `use_joint_state_pub`,
`urdf_file`, `rviz_config_file`.

### Drive around in Gazebo

```bash
ros2 launch autonomous_navigation drive_sim.launch.py
```

Then drive it with **one** of the following, in a separate terminal:

```bash
# keyboard
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
  --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
```

```bash
# joystick (two terminals)
ros2 run joy joy_node
ros2 run teleop_twist_joy teleop_node
```

Pass `joy_device:=/dev/input/js0` if your controller is not on `js2`.

### Autonomous navigation demo

```bash
ros2 launch autonomous_navigation waypoints.launch.py
```

In RViz, click **Nav2 Goal** in the top toolbar and click a target pose on the
map. The rover should plan a path and drive there in Gazebo.

### GPS localisation on the real rover

```bash
ros2 launch autonomous_navigation gps_navsat.launch.py use_sim_time:=false
```

Runs two EKF nodes (`odom` and `map` frames) plus `navsat_transform`, publishing
`odometry/local` and `odometry/global`. Needs GPS and IMU data — see
[`gps_node`](../gps_node).

## Layout

| Directory | Contents |
| --- | --- |
| `urdf/` | Xacro robot description, plus Gazebo plugin macros (lidar, GPS, IMU, `ros2_control`) |
| `config/` | Nav2 params, EKF params (`ekf.yaml`, `dual_ekf_navsat.yaml`), joystick config |
| `world/` | Gazebo worlds (`smalltown.world`, `obstacles.world`, `my_world*.sdf`) |
| `rviz/` | RViz configs (`urdf_config.rviz`, `nav2_config.rviz`) |
| `meshes/` | Visual and collision meshes |

## Troubleshooting

- **RViz / Gazebo will not open in Docker** — use the noVNC web desktop at
  <http://localhost:6080> (`DISPLAY=:1`).
- **`PackageNotFoundError: nav2_bringup`** — install the Nav2 and
  `robot_localization` dependencies: `rosdep install --from-paths src -i -r -y`.
- **Robot does not move in Gazebo** — check that `/diff_cont/cmd_vel_unstamped`
  has a publisher: `ros2 topic info /diff_cont/cmd_vel_unstamped --verbose`.

Gazebo demo walkthrough this package follows: <https://youtu.be/IjFcr5r0nMs>
