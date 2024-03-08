cmake_minimum_required(VERSION 3.8)
project(chassis_controls)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(general_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

add_executable(power_data src/power_data_publisher.cpp)
add_executable(drive_control src/drive_control.cpp)

add_library(
    chassis_controls
    SHARED
    hardware/drive_hardware.cpp)
target_compile_features(chassis_controls PUBLIC c_std_99 cxx_std_17)
target_include_directories(chassis_controls PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/hardware/include>
    $<INSTALL_INTERFACE:include>)
ament_target_dependencies(chassis_controls PUBLIC pluginlib rclcpp_lifecycle hardware_interface rclcpp)

set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR}/lib)
ament_target_dependencies(power_data rclcpp general_interfaces)
ament_target_dependencies(drive_control rclcpp general_interfaces geometry_msgs)
include_directories("${PROJECT_SOURCE_DIR}/include")

pluginlib_export_plugin_description_file(hardware_interface chassis_controls.xml)

install(TARGETS
  power_data
  drive_control
  DESTINATION lib/${PROJECT_NAME})

install(
    DIRECTORY launch description
    DESTINATION share/${PROJECT_NAME})

install(
    PROGRAMS scripts/can_start.sh
    DESTINATION lib/${PROJECT_NAME})

install(
    DIRECTORY hardware/include/
    DESTINATION include/chassis_controls)

install(TARGETS chassis_controls
    EXPORT chassis_controls
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin)

if (${CMAKE_LIBRARY_ARCHITECTURE} STREQUAL "arm-linux-gnueabihf") # Jetson TK1 / Pi
    set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/arm32)
elseif (${CMAKE_LIBRARY_ARCHITECTURE} STREQUAL "aarch64-linux-gnu") # Jetson TX2
    set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/arm64)
else()
    set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/x86-64) # Developing on VM
endif()

target_link_libraries(power_data ${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so)
target_link_libraries(power_data ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so)
target_link_libraries(power_data ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so)

target_link_libraries(drive_control ${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so)
target_link_libraries(drive_control ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so)
target_link_libraries(drive_control ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so)


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

ament_export_targets(chassis_controls HAS_LIBRARY_TARGET)
ament_export_dependencies(
    ament_cmake
    rclcpp
    general_interfaces
    geometry_msgs
    pluginlib
    hardware_interface
    rclcpp_lifecycle)
ament_package()
