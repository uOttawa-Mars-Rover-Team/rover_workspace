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
find_package(xacro REQUIRED)

if(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR STREQUAL "armv7l") # 32 bit Arm Linux
  set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/arm32)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR STREQUAL "aarch64") # 64 bit Arm Linux
  set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/arm64)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux" AND CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64") # x86-64 Linux
  set(PHOENIX_LIBS_DIR ${CMAKE_SOURCE_DIR}/lib/x86-64)
else()
  message(WARNING "Detected ${CMAKE_SYSTEM_NAME} and ${CMAKE_SYSTEM_PROCESSOR}")
  message(FATAL_ERROR "Unsupported system.")
endif()

add_executable(drive_test src/drive_test.cpp)
target_link_libraries(
    drive_test
    ${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so
    ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so
    ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so
)
ament_target_dependencies(drive_test rclcpp general_interfaces geometry_msgs)

add_library(${PROJECT_NAME} SHARED src/drive_hardware.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC c_std_99 cxx_std_17)
target_include_directories(
    ${PROJECT_NAME}
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)
target_link_libraries(
    ${PROJECT_NAME}
    PUBLIC
    ${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so
    ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so
    ${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so
)
ament_target_dependencies(${PROJECT_NAME} PUBLIC rclcpp pluginlib rclcpp_lifecycle hardware_interface)
pluginlib_export_plugin_description_file(hardware_interface chassis_controls.xml)

set(CMAKE_BINARY_DIR ${CMAKE_SOURCE_DIR}/bin)
set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR}/lib)
include_directories(${PROJECT_SOURCE_DIR}/include)

install(
    TARGETS
    drive_test
    DESTINATION lib/${PROJECT_NAME}
)

install(
    PROGRAMS scripts/can_start.sh
    DESTINATION lib/${PROJECT_NAME}
)

install(
    DIRECTORY
    launch
    description
    config
    DESTINATION share/${PROJECT_NAME}
)

install(
    DIRECTORY include/
    DESTINATION include
)

install(
    TARGETS chassis_controls
    EXPORT chassis_controls
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib
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

ament_export_targets(${PROJECT_NAME} HAS_LIBRARY_TARGET)
ament_export_dependencies(
    ament_cmake
    rclcpp
    general_interfaces
    geometry_msgs
    pluginlib
    hardware_interface
    rclcpp_lifecycle
    xacro
)
ament_package()
