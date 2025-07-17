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

add_library(phoenix_core SHARED IMPORTED)
set_target_properties(phoenix_core PROPERTIES
  IMPORTED_LOCATION "${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so"
)

add_library(phoenix_tools SHARED IMPORTED)
set_target_properties(phoenix_tools PROPERTIES
  IMPORTED_LOCATION "${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so"
)

add_library(phoenix_cci SHARED IMPORTED)
set_target_properties(phoenix_cci PROPERTIES
  IMPORTED_LOCATION "${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so"
)

# --- drive_test executable ---
add_executable(drive_test src/drive_test.cpp)
# --- NEW: Add include directories for the executable's dependencies ---
target_include_directories(
    drive_test
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${rclcpp_INCLUDE_DIRS}
    ${general_interfaces_INCLUDE_DIRS}
    ${geometry_msgs_INCLUDE_DIRS}
)
target_link_libraries(
    drive_test
    PRIVATE # Use PRIVATE for executables
    phoenix_core
    phoenix_tools
    phoenix_cci
    ${rclcpp_LIBRARIES}
    ${general_interfaces_LIBRARIES}
    ${geometry_msgs_LIBRARIES}
)


# --- chassis_controls library ---
add_library(${PROJECT_NAME} SHARED src/drive_hardware.cpp)
target_compile_features(${PROJECT_NAME} PUBLIC c_std_99 cxx_std_17)
# --- MODIFIED: Add dependency include directories to the library ---
target_include_directories(
    ${PROJECT_NAME}
    PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
    # Add dependency includes here. PUBLIC is correct because your public
    # header drive_hardware.hpp includes them.
    ${rclcpp_INCLUDE_DIRS}
    ${pluginlib_INCLUDE_DIRS}
    ${rclcpp_lifecycle_INCLUDE_DIRS}
    ${hardware_interface_INCLUDE_DIRS}
)
target_link_libraries(
    ${PROJECT_NAME}
    PUBLIC # PUBLIC is correct here
    phoenix_core
    phoenix_tools
    phoenix_cci
    ${rclcpp_LIBRARIES}
    ${pluginlib_LIBRARIES}
    ${rclcpp_lifecycle_LIBRARIES}
    ${hardware_interface_LIBRARIES}
)
pluginlib_export_plugin_description_file(hardware_interface chassis_controls.xml)

# --- Installs are correct ---

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

install(
    FILES
    "${PHOENIX_LIBS_DIR}/libCTRE_Phoenix.so"
    "${PHOENIX_LIBS_DIR}/libCTRE_PhoenixTools.so"
    "${PHOENIX_LIBS_DIR}/libCTRE_PhoenixCCI.so"
    DESTINATION lib
    PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)


if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
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
