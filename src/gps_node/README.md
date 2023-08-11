# ROS Package: gps\_node

## Info

__Messages:__ gps.msg (topic: GPS), imu.msg (topic: IMU), sensor_msgs/Imu (topic: /imu/sensor/data), 
sensor_msgs/NavSatFix (topic: /gps/sensor/data), and all messages published by robot_localization, most importantly: 
nav_msgs/Odometry (topic: odom/filtered/)

__Scripts:__ GPS\_ros\_node.py

__Maintainers:__ Angelica

__Prerequisites & Hardware Setup:__ This node must connect to an Arduino running the GPS\_IMU\_No\_ROSserial.ino sketch in the arduino_sketches folder. See Pinout comment in GPS\_IMU\_No\_ROSserial.ino sketch. Install robot\_localization by running 
`sudo apt-get install ros-melodic-robot-localization`

__Extra Info:__ The script, GPS\_ros\_node.py, takes one optional parameter for the serial port the Arduino Uno is connected to. If 
omitted the script uses the default port: `/dev/ttyACM0`

## Description

The gps\_node is responsible for the data from the GPS and IMU and the Kalman filter which attempts to clean both of their outputs. The package has two launch files: gps\_node.launch (which runs just the GPS and IMU node) and kalman.launch (which also launches the Kalman filter nodes).

gps\_node is a ROS node that runs both the GPS and IMU publishers. It connects to an Arduino that is running the GPS\_IMU\_No\_ROSserial.ino sketch in the arduino\_sketches folder via USB. The other sketches (rover\_both, Rover\_GPS, Rover\_IMU) in the arduino\_sketches folder are previous versions of the arduino sketch to be used with this node and are left in case they will be useful in the future.   

The Arduino collects the information from the sensors and sends it via USB (serial port in the code) to the gps\_node. The node's script, GPS\_ros\_node.py, reads from the serial port, formats the data, and send the filled out gps.msg, imu.msg, sensor_msgs/Imu and sensor_msgs/NavSatFix messages. All messages are sent out about once per second. The sensor_msgs/Imu and sensor_msgs/NavSatFix messages are used by the kalman filter. The kalman filter outputs lots of different messages (one of those is a diagnostic message) but we mostly just care about the nav_msgs/Odometry message as this is what will be fed into our localization and mapping software. For more information about robot_localization please reference the link provided in the Helpful Resources section of this Readme.

#### Additional Info about GPS.msg and IMU.msg

The imu.msg contains the three 32-bit floats for roll, pitch and yaw, calculated from the measurements on the IMU. The gps.msg message contains an unsigned 8-bit int that will be 1 if the GPS has a fix and 0 if not. It also has another unsigned 8-bit int with the number of satellites the GPS is receiving from. Lastly, the message also includes two 32-bit floats, one for the latitude and one for the longitude. If the fix is 0 these will both be 0.0 and should be ignored, otherwise they will contain the coordinates given by the GPS. These coordinates will be in decimal degrees.

The GPS itself outputs coordinates in a strange format as follows:\
Latitude will be negative if it is south and positive if it is north. Longitude will be negative if it is west and positive if it is east. The floats should be converted into coordinates in degrees and minutes as follows from the Adafruit website, "Latitude: DDMM.MMMM (The first two characters are the degrees) Longitude: DDMM.MMMM (The first two characters are the degrees)". For more information on converting the floats to coordinates please visit [this page.](https://learn.adafruit.com/adafruit-ultimate-gps/direct-computer-wiring/)

## Helpful Resources:

The wiki page for GPS on GitLab: https://gitlab.com/uorover/rover_workspace/-/wikis/GPS-Research-for-Rover/   
The adafruit pages on the GPS module: https://learn.adafruit.com/adafruit-ultimate-gps/   
The sparkfun pages on the IMU module: https://learn.sparkfun.com/tutorials/lsm9ds1-breakout-hookup-guide/all  
The home page for the robot_localization documentation: http://docs.ros.org/en/melodic/api/robot_localization/html/index.html 


