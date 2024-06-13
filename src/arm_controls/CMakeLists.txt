set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
cmake_minimum_required(VERSION 3.8)
project(arm_controls)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(general_interfaces REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)


add_library(
    arm_hardware
    SHARED
    hardware/arm_hardware.cpp
    )

#### UNCOMMENT WHEN WE CREATE ARM_CONTROLS NODE ####

target_include_directories(arm_hardware PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
    )

#target_compile_features(arm_controls PUBLIC c_std_99 cxx_std_17)

#ament_target_dependencies(
#    arm_controls
#    "moveit_ros_planning_interface"
#    "rclcpp"
#    "general_interfaces"
#    )

#install(TARGETS arm_controls
#    DESTINATION lib/${PROJECT_NAME}
#    )

ament_target_dependencies(
    arm_hardware PUBLIC
    "pluginlib"
    "rclcpp_lifecycle"
    "hardware_interface"
    "general_interfaces"
    "rclcpp"
    )

pluginlib_export_plugin_description_file(hardware_interface arm_hardware.xml)


install(
    DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}
    )
install(
    DIRECTORY config
    DESTINATION share/${PROJECT_NAME}
    )


install(
    DIRECTORY include/${PROJECT_NAME}/
    DESTINATION include)

install(TARGETS arm_hardware
    EXPORT arm_hardware
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib
)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)

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

ament_export_targets(arm_hardware HAS_LIBRARY_TARGET)
ament_package()
