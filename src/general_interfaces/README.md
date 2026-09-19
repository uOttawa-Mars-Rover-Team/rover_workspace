# general_interfaces

Custom ROS 2 messages, services, and actions shared by every other package in
this workspace. This package contains no nodes and nothing to launch — it only
generates interface types.

## Build

```bash
colcon build --packages-select general_interfaces
source install/setup.bash
```

Any package that uses these types must be rebuilt after this one changes.

## Interfaces

| Kind | Files |
| --- | --- |
| Messages (`msg/`) | `ArmControl`, `ArmError`, `ArmGpio`, `ArmPose`, `ArmState`, `DriveControl`, `DriveSensor`, `GPS`, `GripperControl`, `IMU`, `MotorData`, `PowerData`, `ReferencePositions`, `ToggleMessage` |
| Services (`srv/`) | `SaveImage`, `CreatePanorama` |
| Actions (`action/`) | `ZeroArm` |

Inspect one at runtime with:

```bash
ros2 interface show general_interfaces/msg/GPS
```

> Note: `DriveSensor.msg` and `ReferencePositions.msg` exist on disk but are not
> listed in `CMakeLists.txt`, so they are **not** built. Add them there if you
> need them.

## Adding a new interface

1. Add the definition under `msg/`, `srv/`, or `action/`.
2. Add its path to the `rosidl_generate_interfaces()` call in `CMakeLists.txt`.
3. Rebuild this package, then rebuild anything that consumes it.

Field types and naming rules are in the
[ROS 2 custom interfaces tutorial](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html).

## Why a separate package?

Keeping interfaces in one place avoids circular/messy dependencies: if a message
lived in package `A` and were used by `B` and `C`, both would need to depend on
`A`. It is also an `ament_cmake` package rather than `ament_python` because
`rosidl` interface generation requires CMake — no C++ knowledge is needed to add
a message.
