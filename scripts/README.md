# scripts

Host setup and convenience scripts. These run on **Linux**; if you are using the
[dev container](../.devcontainer) you do not need most of them.

| Script | What it does |
| --- | --- |
| `full_setup.sh` | Full native setup — run this once on a fresh Ubuntu machine. Calls the three scripts below in order |
| `install_ros_humble.sh` | Installs ROS from apt |
| `install_external_packages.sh` | Installs Node.js 22 (for the dashboard), pip, and all `package.xml` dependencies via `rosdep` |
| `build_project.sh` | Sources ROS and runs `colcon build` in `~/rover_workspace` |
| `Vagrantfile` | Vagrant VM definition, an alternative to Docker for non-Linux hosts |
| `servo_control/` | Standalone servo experiments: `joy_servo_test.py` (ROS-side joystick test) and `servo_control.ino` (matching Arduino sketch) |

## Usage

```bash
cd ~/rover_workspace/scripts
./full_setup.sh
```

Then, from the workspace root:

```bash
colcon build
source install/setup.bash
```

> These scripts still reference ROS Humble and hardcode `~/rover_workspace` as
> the workspace path, while the dev container is on **Jazzy**. Prefer the dev
> container unless you specifically need a native install.
