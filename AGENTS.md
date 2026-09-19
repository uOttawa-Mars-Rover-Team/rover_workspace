# AGENTS.md

Guidance for AI coding agents working in this repository. Humans should start
with [`README.md`](README.md).

## What this is

A ROS 2 **Jazzy** colcon workspace for the uOttawa Mars Rover, plus a PlatformIO
firmware project and a React dashboard.

```
src/                        ROS 2 packages (colcon builds these)
  autonomous_navigation/    Gazebo sim, Nav2, EKF localisation  (ament_python)
  chassis_controls/         Drive system, CTRE/CAN, teleop       (ament_cmake)
  general_interfaces/       Shared msg/srv/action definitions    (ament_cmake)
  gps_node/                 GPS + IMU publishing                 (ament_python)
  robotic_arm_controls/     Arm teleop and IK                    (ament_python)
  dashboard/                React + Vite web dashboard (NOT a ROS package)
rover_embedded_shield/      Arduino Mega firmware (PlatformIO)
scripts/                    Native Linux setup scripts
.devcontainer/              ROS 2 Jazzy dev container (recommended environment)
build/ install/ log/        Build output — never edit or commit
```

Each directory listed above has its own `README.md`. Read the relevant one before
changing code in it.

## Ground rules

- **Never edit `build/`, `install/`, `log/`, or `.ccache/`.** They are generated,
  and contain stale packages (`arm_controls`, `arm_urdf`, `camera_nodes`,
  `ld_controls`, `ld_sensor_array`) that no longer exist in `src/`. Do not treat
  anything in there as source of truth.
- **Don't run `colcon build` on a Windows host.** The build only works inside the
  dev container or on Linux. If you need to verify a change on Windows, read the
  code — do not attempt a build and report the failure as a code problem.
- **ROS distro is Jazzy.** Some scripts and docs still say Humble; that is known
  drift, not something to "fix" opportunistically.
- **Work on a branch.** `master` is kept functional; features go on their own
  branch (the usual PR target is `ros2-testing`).
- Commit only source. Nothing in `build/`, `install/`, `log/`, `node_modules/`,
  or `.pio/`.

## Build and run

Inside the dev container (or on native Linux), from the workspace root:

```bash
colcon build                                  # everything
colcon build --packages-select <pkg>          # one package
colcon build --packages-up-to <pkg>           # a package and its deps
source install/setup.bash                     # required in every new shell
```

Use `--symlink-install` when iterating on Python packages so edits take effect
without a rebuild.

After changing `general_interfaces`, rebuild every package that consumes it —
stale generated headers cause confusing runtime errors.

Install new `package.xml` dependencies with:

```bash
rosdep install --from-paths src -i -r -y
```

Other subprojects have their own toolchains:

```bash
cd src/dashboard      && npm install && npm run dev     # dashboard
cd rover_embedded_shield && pio run -e AppRA            # firmware
```

## Tests and linting

The ROS packages use the standard ament setup (`ament_lint_auto`, `pytest`):

```bash
colcon test --packages-select <pkg>
colcon test-result --verbose
```

Test coverage is thin — the `test/` directories mostly contain the default
`ament_copyright` / `flake8` / `pep257` linter stubs. Do not claim behaviour is
verified because `colcon test` passed.

Python style follows what the existing code does: 4-space indent, double quotes,
`snake_case`. `autonomous_navigation` and `gps_node` are Black/isort-formatted;
`robotic_arm_controls` is not — match the file you are editing rather than
reformatting it.

## Conventions

- **Nodes and launch files.** Python packages register executables in
  `setup.py` → `entry_points.console_scripts`; `ament_cmake` packages register
  them via `install(TARGETS ...)` / `install(PROGRAMS ...)` in `CMakeLists.txt`.
  Adding a node means adding it there too, or `ros2 run` will not find it.
- **New launch files** must be picked up by the package's install rules. Note
  that `gps_node` and `robotic_arm_controls` glob `*launch.[pxy][yma]*`, so a
  file must be named `<something>.launch.py` to be installed;
  `autonomous_navigation` globs `launch/*.py`.
- **Custom messages go in `general_interfaces`**, not in the consuming package,
  and must be added to `rosidl_generate_interfaces()` in its `CMakeLists.txt`.
- **Launch file naming** in `robotic_arm_controls` is
  `<where-it-runs>_<control-mode>.launch.py` (`development_`, `basestation_`,
  `roverpc_`).
- **Velocity command topics** are arbitrated by `twist_mux`. Publish to a named
  source topic (`/cmd_vel_teleop`, `/cmd_vel_keyboard`, …) and let `twist_mux`
  forward the winner to `/diff_cont/cmd_vel_unstamped`. Do not publish directly
  to the output topic.

## Known broken / incomplete things

Do not "discover" these as bugs — they are already known:

- `robotic_arm_controls` launch files ending in `_ik_servo` / `_ik_gui` include
  launch files from an `arm_controls` package that is not in `src/`. They fail
  with `PackageNotFoundError`.
- `gps_node`'s `setup.py` declares a `gps_node` executable whose module
  (`gps_node/gps_node.py`) is missing.
- `general_interfaces` has `DriveSensor.msg` and `ReferencePositions.msg` on
  disk that are not listed in `CMakeLists.txt`, so they are not built.
- `chassis_controls/README_testing.md` history mentions a `drive_control` node;
  only `drive_test` is built.
- A phantom `joy_node` on the Jetson interferes with laptop teleop. See
  `src/chassis_controls/ControllerREADME.md`.

## Hardware caveats

Much of this workspace only runs meaningfully with hardware attached: CAN bus and
CTRE Talons (`chassis_controls`), a u-blox receiver (`gps_node`), serial-attached
microcontrollers (`robotic_arm_controls`, `rover_embedded_shield`), and gamepads.
When you cannot test against hardware, say so explicitly rather than implying a
change is verified. `autonomous_navigation` and the dummy publishers in
`gps_node` are the parts that can be exercised without it.

GUI tools (RViz, Gazebo) in the dev container render through the noVNC web
desktop at <http://localhost:6080> (`DISPLAY=:1`).
