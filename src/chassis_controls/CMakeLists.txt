set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
cmake_minimum_required(VERSION 3.8)
project(chassis_controls)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(general_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)


add_executable(power_data src/power_data_publisher.cpp)
add_executable(drive_control src/drive_control.cpp)
set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR}/lib)
ament_target_dependencies(power_data rclcpp general_interfaces)
ament_target_dependencies(drive_control rclcpp general_interfaces geometry_msgs)


include_directories("${PROJECT_SOURCE_DIR}/include")


install(TARGETS
  power_data
  drive_control
  DESTINATION lib/${PROJECT_NAME})

install(
    DIRECTORY launch
    DESTINATION share/${PROJECT_NAME})

install(
    PROGRAMS scripts/can_start.sh
    DESTINATION lib/${PROJECT_NAME})

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

ament_package()
