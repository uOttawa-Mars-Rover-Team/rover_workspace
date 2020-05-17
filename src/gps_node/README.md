# ROS Package: gps\_node

## Info

__Messages:__ gps.msg, imu.msg

__Scripts:__ GPS\_ros\_node.py

__Maintainers:__ Angelica

__Prerequisite:__ This node must connect to an Arduino running the GPS\_IMU\_No\_ROSserial.ino sketch in the arduino_sketches folder.

__Extra Info:__

## Description

gps\_node is a ROS node that runs both the GPS and IMU publishers. It connects to an arduino via the serial port that is running the GPS\_IMU\_No\_ROSserial.ino sketch in the arduino\_sketches folder. The other sketches (rover\_both, Rover\_GPS, Rover\_IMU) in the arduino\_sketches folder are previous versions of the arduino sketch to be used with this node and are left in case they will be useful in the future.   

The Arduino collects the information from the sensors and sends it via the serial port to the gps\_node. The node's script GPS\_ros\_node.py reads from the serial port, formats the data, and send the filled out gps.msg and imu.msg messages. The gps.msg message is sent under the GPS topic about every 2 seconds. The imu.msg message is sent under the IMU topic about every 2 seconds as well.   

The imu.msg contains the three 32-bit floats for roll, pitch and yaw, calculated from the measurements on the IMU. The gps.msg message contains an unsigned 8-bit int that will be 1 if the GPS has a fix and 0 if not. It also has another unsigned 8-bit int with the number of satellites the GPS is receiving from. Lastly, the message also includes two 32-bit floats, one for the latitude and one for the longitude. If the fix is 0 these will both be 0.0 and should be ignored, otherwise they will contain the coordinates given by the GPS. Latitude will be negative if it is south and positive if it is north. Longitude will be negative if it is west and positive if it is east. The floats should be converted into coordinates in degrees and minutes as follows from the Adafruit website, "Latitude: DDMM.MMMM (The first two characters are the degrees) Longitude: DDMM.MMMM (The first two characters are the degrees)". For more information on converting the floats to coordinates please visit [this page.](https://learn.adafruit.com/adafruit-ultimate-gps/direct-computer-wiring/)

## Helpful Resources:

The wiki page for GPS on GitLab: https://gitlab.com/uorover/rover_workspace/-/wikis/GPS-Research-for-Rover/   
The adafruit pages on the GPS module: https://learn.adafruit.com/adafruit-ultimate-gps/   
The sparkfun pages on the IMU module: https://learn.sparkfun.com/tutorials/lsm9ds1-breakout-hookup-guide/all   


