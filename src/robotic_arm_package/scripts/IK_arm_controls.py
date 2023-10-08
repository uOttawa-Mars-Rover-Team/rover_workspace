#!/usr/bin/python
import rospy
import serial
import struct
import numpy as np
import array

from sensor_msgs.msg import Joy
from std_msgs.msg import String

class IKController:
    def __init__(self):
        #                dX, dY, dZ, WP, WR, EE
        self.movements = [0,  0,  0,  0,  0,  0]

        # Default Constants
        self.DEADBAND = 0.35
        self.MULTIPLIER = 1

        # Axes indices
        self.X_AXIS = 1
        self.Y_AXIS = 0
        self.Z_AXIS = 3
        self.WRIST_PITCH = 5
        self.WRIST_ROLL = 4

        # Button indices
        self.EE_CLOSE_BTN = 0
        self.EE_OPEN_BTN = 1

        # Speed toggles
        self.HALF_SPEED_BTN = 6
        self.NORM_SPEED_BTN = 7
        self.ONEPFIVE_SPEED_BTN = 8
        self.DOUBLE_SPEED_BTN = 9

        # Joy subscriber
        self.joy_sub = rospy.Subscriber("/joy", Joy, self.joy_callback)

        # ik_msg publisher
        self.ik_control_pub = rospy.Publisher("/ik_msg", String, queue_size=1000)

        # Serial settings
        #self.ARDUINO = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

    # Send to IK
    def write_serial(self):

        self.ik_control_pub.publish(self.movements)
        rospy.loginfo("Sent to IK: "+str(self.movements))

    def joy_callback(self, data):

        self.movements = [0,  0,  0,  0,  0,  0]

        '''
        if data.buttons[self.HALF_SPEED_BTN]:
            self.MULTIPLIER = 3
            rospy.loginfo("Speed multiplier changed to 12.5%")
        elif data.buttons[self.HALF_SPEED_BTN]:
            self.MULTIPLIER = 2
            rospy.loginfo("Speed multiplier changed to 25%")
        elif data.buttons[self.NORM_SPEED_BTN]:
            self.MULTIPLIER = 1
            rospy.loginfo("Speed multiplier changed to 50%")
        elif data.buttons[self.DOUBLE_SPEED_BTN]:
            self.MULTIPLIER = 0
            rospy.loginfo("Speed multiplier changed to 100%")
        '''
        # Main axes:
        # Big stick forward/backward
        if (abs(data.axes[self.X_AXIS]) >= self.DEADBAND):
            self.movements[0] = int(data.axes[self.X_AXIS] * 1000) >> self.MULTIPLIER
        # Big stick side-to-side
        if (abs(data.axes[self.Y_AXIS]) >= self.DEADBAND):
            self.movements[1] = int(data.axes[self.Y_AXIS] * 1000) >> self.MULTIPLIER
        '''# Dial up/down
        if (abs(data.axes[self.Z_AXIS]) >= self.DEADBAND):
            self.movements[2] = int(data.axes[self.Z_AXIS] * 1000) >> self.MULTIPLIER

        # Wrist
        # Small joy up/down
        if (abs(data.axes[self.WRIST_PITCH]) >= self.DEADBAND):
            self.movements[3] = int((data.axes[self.WRIST_PITCH] / 2.0) * self.MULTIPLIER * 10)
        # Small joy side-to-side
        if (abs(data.axes[self.WRIST_ROLL]) >= self.DEADBAND):
            self.movements[4] = int((data.axes[self.WRIST_ROLL] / 2.0) * self.MULTIPLIER * 10)
        '''
        # End-effector
        # Front trigger: close
        if data.buttons[self.EE_CLOSE_BTN]:
            self.movements[5] = 16 >> self.MULTIPLIER
        # Thumb trigger: open
        if data.buttons[self.EE_OPEN_BTN]:
            self.movements[5] = 16 >> self.MULTIPLIER
        
        # MOVE ARM
        self.write_serial()

if __name__ == '__main__':
    rospy.init_node("IK_arm_controls")
    rospy.loginfo("IK_arm_controls node started")
    controller = IKController()
    rospy.spin()