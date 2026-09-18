cmake_minimum_required(VERSION 3.8)
project(serial_ros2_testing)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)

# Include directories
include_directories(
  src/arm_controls/serial_communication_library/include
  ${rclcpp_INCLUDE_DIRS}
  ${sensor_msgs_INCLUDE_DIRS}
)

set(target_dependencies
  "rclcpp"
  "sensor_msgs"
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


get_filename_component(PARENT_DIR ${CMAKE_CURRENT_SOURCE_DIR} DIRECTORY)
get_filename_component(PARENT_DIR ${PARENT_DIR} DIRECTORY)
get_filename_component(PARENT_DIR ${PARENT_DIR} DIRECTORY)
set(SERIAL_COMM_LIB_PATH "${PARENT_DIR}/serial_communication_library")

add_subdirectory(${SERIAL_COMM_LIB_PATH} ${CMAKE_BINARY_DIR}/serial_communication_library_build)

add_executable(listener src/test_serial_node.cpp)


target_link_libraries(listener ${rclcpp_LIBRARIES} ${sensor_msgs_LIBRARIES} serial_comms)

install(TARGETS
  listener
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()