cmake_minimum_required(VERSION 3.10)

project(serial_comms LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories for both external and internal serial lib
include_directories(third_party/SerialLibrary/include)
include_directories(include) 

# Source files for internal serial lib
set(serial_comms_SRCS
  src/serial_communication.cpp  
)

# Source files for external serial lib
set(serial_SRCS
  third_party/SerialLibrary/src/serial.cc
  third_party/SerialLibrary/include/serial/serial.h
  third_party/SerialLibrary/include/serial/v8stdint.h
  third_party/SerialLibrary/src/impl/list_ports/list_ports_linux.cc
  third_party/SerialLibrary/src/impl/unix.cc
)

# Add the serial library 
add_library(serial ${serial_SRCS})
target_link_libraries(serial rt)

# Add the serial_comms library 
add_library(serial_comms ${serial_comms_SRCS})
target_link_libraries(serial_comms serial rt)

# Add and link Google Test library
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# Add test executable
add_executable(serial_comms_tests testing/test.cpp)
target_link_libraries(serial_comms_tests serial_comms ${GTEST_LIBRARIES} pthread)

# Enable CTest for running tests
enable_testing()
add_test(NAME SerialCommsTests COMMAND serial_comms_tests)

install(TARGETS serial_comms
    	EXPORT serial_comms
    	ARCHIVE DESTINATION lib
    	LIBRARY DESTINATION lib
    	RUNTIME DESTINATION lib
)

install(TARGETS serial
    	EXPORT serial
    	ARCHIVE DESTINATION lib
    	LIBRARY DESTINATION lib
    	RUNTIME DESTINATION lib
)


# Cmake with more clear names to differentiate between internal and external serial libraries
# caused issues regarding nested cmakes
#[[
cmake_minimum_required(VERSION 3.10)

project(serial_comms LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories for both external and internal serial lib
include_directories(third_party/SerialLibrary/include)
include_directories(include) 

# Source files for internal serial lib
set(serial_internal_SRCS
  src/serial_communication.cpp  
)

# Source files for external serial lib
set(serial_external_SRCS
  third_party/SerialLibrary/src/serial.cc
  third_party/SerialLibrary/include/serial/serial.h
  third_party/SerialLibrary/include/serial/v8stdint.h
  third_party/SerialLibrary/src/impl/list_ports/list_ports_linux.cc
  third_party/SerialLibrary/src/impl/unix.cc
)

# Add the external serial library 
add_library(serial_external_lib ${serial_external_SRCS})
target_link_libraries(serial_external_lib rt)

# Add the internal serial library 
add_library(serial_internal_lib ${serial_internal_SRCS})
target_link_libraries(serial_internal_lib serial_external_lib rt)

# Add and link Google Test library
find_package(GTest REQUIRED)
include_directories(${GTEST_INCLUDE_DIRS})

# Add test executable
add_executable(serial_tests testing/test.cpp)
target_link_libraries(serial_tests serial_internal_lib ${GTEST_LIBRARIES} pthread)

# Enable CTest for running tests
enable_testing()
add_test(NAME SerialCommsTests COMMAND serial_tests)

install(TARGETS serial_internal_lib
    	EXPORT serial_internal_lib
    	ARCHIVE DESTINATION lib
    	LIBRARY DESTINATION lib
    	RUNTIME DESTINATION lib
)

install(TARGETS serial_external_lib
    	EXPORT serial_external_lib
    	ARCHIVE DESTINATION lib
    	LIBRARY DESTINATION lib
    	RUNTIME DESTINATION lib
)

]]