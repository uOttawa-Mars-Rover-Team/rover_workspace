# ROS Package: life\_detection\_node

## Info

__Messages:__

- Published topics:

    - __/VacHoseCMD__  <std_msgs::UInt8> 
    - __/FunnelFlapCMD__  <std_msgs::Empty> 
    - __/VacMotorCMD__  <std_msgs::UInt8> 
    - __/BeakerCMD__  <std_msgs::UInt8>> 
    - __/AgitateCMD__  <std_msgs::UInt8>>
    - __/WeatherCollectionCMD__  <std_msgs::Empty>> 



__Scripts:__ keyboard\_control.py

__Maintainers:__ Raghav Bhargava

__Prerequisites & Hardware Setup:__ __Prerequisites & Hardware Setup:__ 

Prerequisites for Keyboard Control Script: Install pynput version 1.6.8 python package with:
    ```pip install pynput==1.6.8```

1. Flash microcontroller (Arduino Mega) with the life_detection.ino sketch.

2. Connect the microcontroller via USB to computer/raspberry pi with ros installed

3. Install the rosserial ros package on the connected computer.

    ```sudo apt-get install ros-melodic-rosserial```

4. Launch the roscore if one is not alreay running, open another terminal and run the serial node.

    ```roscore```

    When running the serial node, figure out which port the microcontroller is connected to and specify that information as an input parameter. 

    Example: `/dev/ttyACM0`

    ```rosrun rosserial_python serial_node.py /dev/<ENTER CORRECT PORT INFO>```

    The Life Detection Module should now be ready to listen for incoming commands.

5. Run the Life Detection Control Node, in a new terminal with:

    ```rosrun life_detection_node keyboardControl.py```

## Description

At the time of writing this README (June 14th, 2023), the life detection module currently consists of the following features:

1. A vacuum hose extender/retractor system that lifts and lowers a tube to make contact with the soil. This system is driven by a stepper motor that lifts the hose using a screw. The stepper motor stops turning once the hose triggers either an upper limit swtich or a lower limit switch. In order to operate this function:
    
    ```up and down arrows on the keyboard raise and lower the tube```

2. A vacuum that is used to suck up soil from the ground. The vacuum is toggled (ON/OFF) using a relay.

    ```click "v" key to toggle the vacuum on and off```

3. A vacuum flap that seals the vacuum chamber in order to increase suction. The vacuum chamber has two holes, one hole that connects to the vacuum hose, and other hole at the end of a funnel that serves to deposit the soil in to the beakers. When the vacuum is in operation, the funnel hole is sealed using a servo-actuated cover. Example test:

    ```click "f" key to toggle the funnel flap closed and open```

4. The sample system holds a set of beakers that are used to perform the science experiments. A stepper motor is used to rotate the sample system so that it can position each of the beakers underneath the vacuum funnel (when required).

    ```Use the left and right arrow keys to rotate the sample system a little bit at a time```

5. The sample system must vibrate in order to throughly agitate the samples when they are exposed to the reagent. To achieve this, the stepper motor steps forward and then steps back repeately for a defined duration. Example test:

    ```hold the "a" key to aggitate the sample```

