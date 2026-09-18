# general_interfaces Package

## Purpose

- Define messages, services, and actions that will be used throughout the rest of the workspace

## Adding a new interface

1. Add a message (under `./msg/`), service (under `./srv/`), or action (under `./action/`) definition within this package
2. Add the path to the new interface definition inside the `CMakeLists.txt` file for this package to allow it to be built

## Q&A

- How can I learn more about how to create a custom interface (message/service/action) and about what this package does?

  - Visit the ROS2 (Humble) docs explaining how to create custom interfaces: https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html

- Why can't custom interfaces (message/service/action) be defined in the packages that they are used in?

  - It might be possible to do so. However, this may complicate dependencies for interrelated packages. For example, if an interface is defined in package `A` and used in package `B` and `C`, then both `B` and `C` must have dependencies of package `A` defined in the `package.xml`. This may start to get messy as the codebase grows larger.
  - Also, the tutorial from the ROS2 docs teach how to create custom interfaces in a separate package, so the example given was followed

- Why is this package a C++ (ament_cmake) package and not a Python (ament_python) package?

  - The [docs](https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html) and other online sources seem to imply that interface definition packages can't be Python type packages. However, this is probably fine, since not much, if any, C++ knowledge is required to build a new interface.
