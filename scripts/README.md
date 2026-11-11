# scripts

Host setup and convenience scripts. These run on **Linux**; if you are using the
[dev container](../.devcontainer) you do not need most of them.

| Script | What it does |
| --- | --- |
| `full_setup.sh` | Full native setup — run this once on a fresh Ubuntu machine. Calls the three scripts below in order |
| `install_ros.sh` | Installs ROS from apt and sources it from `~/.bashrc` |
| `install_external_packages.sh` | Installs Node.js 22 (for the dashboard), pip, and all `package.xml` dependencies via `rosdep`. On a Jetson, also installs `can-utils` and adds you to the `dialout` group |
| `build_project.sh` | Sources ROS and runs `colcon build` in the workspace |
| `common.sh` | Helpers shared by the scripts above (OS / ROS distro / Jetson detection). Sourced, not run |
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

The scripts work from wherever the repository is cloned, on both x86-64 and
arm64, and are safe to re-run.

## ROS distro and the Jetson

ROS only publishes apt packages for one Ubuntu release per distro, so the
scripts pick the distro from the OS:

| Ubuntu | Jetson equivalent | ROS distro installed |
| --- | --- | --- |
| 24.04 (noble) | JetPack 7 | **Jazzy** — what this workspace targets |
| 22.04 (jammy) | JetPack 6 | Humble — a fallback; expect to fix things |
| anything else | JetPack 5 and older | none, the scripts stop. Use the [dev container](../.devcontainer) |

Check what a Jetson is running with `lsb_release -a` and
`cat /etc/nv_tegra_release`.

Optional environment variables:

| Variable | Default | Effect |
| --- | --- | --- |
| `ROVER_ROS_DISTRO` | from the Ubuntu release | Force a ROS distro |
| `ROS_INSTALL_TYPE` | `ros-base` on a Jetson, `desktop` elsewhere | Which `ros-<distro>-*` metapackage to install |
| `ROVER_WS` | the clone containing `scripts/` | Workspace to build and source |
| `SKIP_APT_UPGRADE` | unset | Set to `1` to skip `apt-get upgrade` (e.g. to leave L4T packages alone) |

Prefer the dev container unless you specifically need a native install.
