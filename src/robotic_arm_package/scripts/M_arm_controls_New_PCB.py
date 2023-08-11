#!/usr/bin/python

# Imports
import time
import rospy
import serial

# Import msg types for publishers & subscribers
from sensor_msgs.msg import Joy
from std_msgs.msg import String

class MArmController:
    def __init__(self):

        # Msg sent via serial
        self.movement = ""

        # Record previous cmds so as to not repeat them
        self.partsInMotion = ["stop;!"]

        # Default Constants
        self.SLEEP = 0.2         # sleep in secs before sending another cmd
        self.DEADBAND = 0.35      # to recognize as axial movement
        self.ROUND_PRECISION = 3

        # Speed-related
        self.SPEED = 0.5
        self.MULTIPLIER = 0.5
        self.SPEED_DEADBAND = 0.05
        self.MOTOR_CAP = 1000
        self.ACTUATOR_CAP = 600
        self.ACTUATOR = 1
        self.TOWER = 2
        self.SPEED_AXIS = 3
        self.WRIST_ROLL = 4
        self.WRIST_PITCH = 5

        # Buttons indices
        self.EE_CLOSE_BUTTON = 0
        self.EE_OPEN_BUTTON = 1
        self.FORCE_STOP_BUTTON = 10

        # Toggle buttons
        self.HALF_SPEED_BTN = 6
        self.NORM_SPEED_BTN = 7
        self.ONEPFIVE_SPEED_BTN = 8
        self.DOUBLE_SPEED_BTN = 9
        self.ACTUATOR_TOGGLE_BUTTON = 11

        # Toggle default
        self.CURRENT_ACTUATOR = 0 # 0 = arm, 1 = forearm

        # Input: Joy msg
        self.JOY_SUB = rospy.Subscriber("/joy", Joy, self.joy_callback)

        # Output: string msg via serial; ex: "EE;-1;244;!"
        self.ARDUINO = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

    # Executes derived movement from "/joy" topic
    def write_serial(self):
        self.ARDUINO.write(self.movement)
        if self.movement != "stop;!":
            time.sleep(self.SLEEP)

    def joy_callback(self, data):

        # Map: [-1.0, 1.0] -> [0.0, 2.0]
        if data.axes[self.SPEED_AXIS] < 0:
            self.SPEED = 1 - round(abs(data.axes[self.SPEED_AXIS]), self.ROUND_PRECISION)
        else:
            self.SPEED = 1 + round(data.axes[self.SPEED_AXIS], self.ROUND_PRECISION)
	self.SPEED /= 2

        #rospy.loginfo(str(self.SPEED)+" "+str(data.axes[self.ACTUATOR]))
        
        # Speed toggles, 50%, 100%, 150% & 200%
        if data.buttons[self.HALF_SPEED_BTN]:
            self.MULTIPLIER = 0.25
            rospy.loginfo("Speed multiplier changed to 25%")
        elif data.buttons[self.NORM_SPEED_BTN]:
            self.MULTIPLIER = 0.5
            rospy.loginfo("Speed multiplier changed to 50%")
        elif data.buttons[self.ONEPFIVE_SPEED_BTN]:
            self.MULTIPLIER = 0.75
            rospy.loginfo("Speed multiplier changed to 75%")
        elif data.buttons[self.DOUBLE_SPEED_BTN]:
            self.MULTIPLIER = 1.0
            rospy.loginfo("Speed multiplier changed to 100%")

        # LA toggle (0: L1: arm, 1: L2: forearm)
        if data.buttons[self.ACTUATOR_TOGGLE_BUTTON]:
            if self.CURRENT_ACTUATOR:
                self.CURRENT_ACTUATOR = 0
                rospy.loginfo("Actuator toggled to L1")
            else:
                self.CURRENT_ACTUATOR = 1
                rospy.loginfo("Actuator toggled to L2")
        
        # Checking all axes are stationary (less than deadband)
        axes_stationary = True
        for idx, value in enumerate(data.axes):
            # Ignore speed axis
            if (idx != self.SPEED_AXIS) & (abs(value) > self.DEADBAND):
                axes_stationary = False
                break

        # Checking no buttons currently pressed
        buttons_unpressed = True
        if axes_stationary:
            for value in data.buttons:
                if value:
                    buttons_unpressed = False
                    break

        # If both axes & buttons are untouched or if speed dial's low, send the stop cmd
        # Or ignore all conditions and send stop if the force stop button is pressed
        stop_condition = (axes_stationary & buttons_unpressed) or (self.SPEED <= self.SPEED_DEADBAND)
        if ((self.partsInMotion[-1] != "stop;!") & stop_condition) or data.buttons[self.FORCE_STOP_BUTTON]:
            self.partsInMotion = ["stop;!"]
            self.movement = "stop;!"
            rospy.loginfo("Movement msg to serial: "+self.movement)
            self.write_serial()
        
        # At least an axis or button pressed while speed > speed threshold
        elif self.SPEED > self.SPEED_DEADBAND:

            # Temporarily stores values while working with axes
            tmp = 0.0
            
            # Tower
            tmp = data.axes[self.TOWER]
            if abs(tmp) > self.DEADBAND:
                self.movement = "TW;"
                if tmp < 0:
                    self.movement += "-1;"
                else:
                    self.movement += "1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(0.25*self.MOTOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()
            
            # Arm & forearm
            tmp = data.axes[self.ACTUATOR]
            if abs(tmp) > self.DEADBAND:
                if self.CURRENT_ACTUATOR:
                    self.movement = "L2;"
                else:
                    self.movement = "L1;"
                if tmp < 0:
                    self.movement += "-1;"
                else:
                    self.movement += "1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(self.ACTUATOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()
            
            # Wrist Roll
            tmp = data.axes[self.WRIST_ROLL]
            if abs(tmp) > self.DEADBAND:
                self.movement = "WR;"
                if tmp < 0:
                    self.movement += "-1;"
                else:
                    self.movement += "1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(self.MOTOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()

            # Wrist Pitch
            tmp = data.axes[self.WRIST_PITCH]
            if abs(tmp) > self.DEADBAND:
                self.movement = "WP;"
                if tmp < 0:
                    self.movement += "-1;"
                else:
                    self.movement += "1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(self.MOTOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()
            
            # End effector open
            if data.buttons[self.EE_OPEN_BUTTON] == 1 and data.buttons[self.EE_CLOSE_BUTTON] == 0:
                self.movement = "EE;-1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(self.MOTOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()

            # End effector close
            elif data.buttons[self.EE_OPEN_BUTTON] == 0 and data.buttons[self.EE_CLOSE_BUTTON] == 1:
                self.movement = "EE;1;"
                if self.movement not in self.partsInMotion:
                    self.partsInMotion.append(self.movement)
                    self.movement += str(int(self.MOTOR_CAP*self.SPEED*self.MULTIPLIER))+";!"
                    rospy.loginfo("Movement msg to serial: "+self.movement)
                    self.write_serial()
            
if __name__ == '__main__':
    rospy.init_node("M_arm_controls")
    rospy.loginfo("M_arm_controls node started")
    controller = MArmController()
    rospy.spin()
