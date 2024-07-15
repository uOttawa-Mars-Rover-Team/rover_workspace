cmake_minimum_required(VERSION 3.10)

project(serial_comms LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories for both your code and the third-party library
include_directories(third_party/SerialLibrary/include)
include_directories(include) 

# Source files for your code
set(serial_comms_SRCS
  src/serial_communication.cpp  
)

# Source files for the third-party serial library
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
