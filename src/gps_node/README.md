# gps_node package

## Purpose

- This package is meant to house the ROS code that runs the GPS and IMU publishers, which publish data related to the rover's positioning and orientation in space.

- The code in this package was initially migrated from our old `gps_node` package that was meant for ROS Melodic.

## Nodes

### `gps_node` Node

The `gps_node` (in `gps_node/gps_node.py`) ROS node runs both the GPS and IMU publishers. It receives GPS and IMU measurements by reading from an Arduino running `GPS_IMU_No_ROSserial.ino` (from the `arduino_sketches` folder of this repository) over the serial port.

The Arduino reads GPS and IMU data from sensors attached to it and writes this data over its serial port. The `gps_node` node reads reads the GPS and IMU data from the Arduino over the serial port and publishes it on 2 separate ROS topics: the GPS data is published on a topic using a message of type `general_interfaces/GPS` and the IMU data is published onto a topic using a message of type `general_interfaces/IMU`.

The `latitude` and `longitude` values this node reads from the Arduino may be specified using [degrees and decimal minutes](https://en.wikipedia.org/wiki/Geographic_coordinate_conversion), in the format `DDMM.MMMM` (the first two characters are the degrees, everything that follows are minutes). If this is the case, you may want to convert these values into decimal degrees coordinates. Instructions exist online specifying how to do so. For more information on converting from decimal degrees and minutes to decimal degrees please visit [this page](https://learn.adafruit.com/adafruit-ultimate-gps/direct-computer-wiring/).

## Helpful Resources

The wiki page for GPS on GitLab: https://gitlab.com/uorover/rover_workspace/-/wikis/Research/GPS-for-Rover

The Adafruit pages on the GPS module: https://learn.adafruit.com/adafruit-ultimate-gps/

The Sparkfun pages on the IMU module: https://learn.sparkfun.com/tutorials/lsm9ds1-breakout-hookup-guide/all
