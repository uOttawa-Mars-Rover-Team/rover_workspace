cmake_minimum_required(VERSION 3.8)
project(general_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

# Lines added as part of the interface package definition were copied from the docs at:
# https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html
# Added as part of interface CMakeLists.txt definition
find_package(rosidl_default_generators REQUIRED)

# Added as part of interface CMakeLists.txt definition
rosidl_generate_interfaces(${PROJECT_NAME}
  "srv/SaveImage.srv"
  "srv/CreatePanorama.srv"
  "msg/ArmControl.msg"
  "msg/GPS.msg"
  "msg/IMU.msg"
  "msg/PowerData.msg"
  "msg/MotorData.msg"
  "msg/DriveControl.msg"
  "msg/ArmPose.msg"
  "msg/ToggleMessage.msg"
  "msg/ArmState.msg"
  "msg/ArmError.msg"
  "action/ZeroArm.action"
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
