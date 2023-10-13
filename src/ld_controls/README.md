# ROS Package: ld_controls

This package is meant to house code that allows for control of the life detection subsystem on the rover.

The code in this package was initially migrated from our old `life_detection_node` package that was meant for ROS Melodic.

## Info

**Messages:**

- Published topics:

  - **/VacHoseCMD** <std_msgs::UInt8>
  - **/FunnelFlapCMD** <std_msgs::Empty>
  - **/VacMotorCMD** <std_msgs::UInt8>
  - **/BeakerCMD** <std_msgs::UInt8>>
  - **/AgitateCMD** <std_msgs::UInt8>>
  - **/WeatherCollectionCMD** <std_msgs::Empty>>

**Scripts:** keyboard_control.py
**Maintainers:** Raghav Bhargava

## Prerequisites & Hardware Setup:

Prerequisites for Keyboard Control Script: Install pynput with rosdep. Run the following command at the root of the repo to ensure it's installed, as well as install dependencies for other packages:

```bash
rosdep install --from-paths src --ignore-src -r -y
```

### Note: Some of the instructions below reference `rosserial`, which is no longer available on ROS2. These instructions are just left in just for reference, however, they should eventually be updated by the package maintainer (currently _Raghav Bhargava_)

1. Flash microcontroller (Arduino Mega) with the `life_detection.ino` sketch.

2. Connect the microcontroller via USB to computer/raspberry pi with ros installed

3. Install the rosserial ros package on the connected computer.

   `sudo apt-get install ros-melodic-rosserial`

4. Launch the roscore if one is not alreay running, open another terminal and run the serial node.

   `roscore`

   When running the serial node, figure out which port the microcontroller is connected to and specify that information as an input parameter.

   Example: `/dev/ttyACM0`

   `rosrun rosserial_python serial_node.py /dev/<ENTER CORRECT PORT INFO>`

   The Life Detection Module should now be ready to listen for incoming commands.

5. Run the Life Detection Control Node, in a new terminal with:

   `rosrun life_detection_node keyboardControl.py`

## Description

At the time of writing this README (June 14th, 2023), the life detection module currently consists of the following features:

1. A vacuum hose extender/retractor system that lifts and lowers a tube to make contact with the soil. This system is driven by a stepper motor that lifts the hose using a screw. The stepper motor stops turning once the hose triggers either an upper limit swtich or a lower limit switch. In order to operate this function:

   `up and down arrows on the keyboard raise and lower the tube`

2. A vacuum that is used to suck up soil from the ground. The vacuum is toggled (ON/OFF) using a relay.

   `click "v" key to toggle the vacuum on and off`

3. A vacuum flap that seals the vacuum chamber in order to increase suction. The vacuum chamber has two holes, one hole that connects to the vacuum hose, and other hole at the end of a funnel that serves to deposit the soil in to the beakers. When the vacuum is in operation, the funnel hole is sealed using a servo-actuated cover. Example test:

   `click "f" key to toggle the funnel flap closed and open`

4. The sample system holds a set of beakers that are used to perform the science experiments. A stepper motor is used to rotate the sample system so that it can position each of the beakers underneath the vacuum funnel (when required).

   `Use the left and right arrow keys to rotate the sample system a little bit at a time`

5. The sample system must vibrate in order to throughly agitate the samples when they are exposed to the reagent. To achieve this, the stepper motor steps forward and then steps back repeately for a defined duration. Example test:

   `hold the "a" key to aggitate the sample`
