#!/usr/bin/python
import rospy
import serial
import struct
import numpy as np

from sensor_msgs.msg import Joy

class IKController:
    def __init__(self):
        self.movements = {
            'X_AXIS': 0,
            'Y_AXIS': 0,
            'Z_AXIS': 0,
            'WRIST_PITCH': 0,
            'WRIST_ROLL': 0,
            'GRIP': 0
        }

        # Default Constants
        self.DEADBAND = 0.2
        self.MULTIPLIER = 1.0

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

        # Subscribers
        self.joy_sub = rospy.Subscriber("/joy", Joy, self.joy_callback)

        # Serial settings
        #baudrate = rospy.get_param('~baudrate', 9600) #default 9600
        #self.serialDev = serial.Serial(baudrate=baudrate)
        #self.serialDev.port = rospy.get_param("~serial_device")
        #self.serialDev.open()

    # Send via serial to MEGA the required
    # units to move in the x, y &/or z dir.
    def write_serial(self):

        # TODO: - publish X/Y/Z AXIAL MOVEMENT TO IK
        #       - publish (serial) WRIST & GRIP MOVEMENT
        rospy.loginfo('Movements:%s\n' % self.movements)
        axial = struct.pack("<ffffff",
                                    self.movements['X_AXIS'],
                                    self.movements['Y_AXIS'],
                                    self.movements['Z_AXIS'],
                                    self.movements['WRIST_PITCH'],
                                    self.movements['WRIST_ROLL'],
                                    self.movements['GRIP']
                                )

        #self.serialDev.write(serial_data)

    def joy_callback(self, data):

        self.movements['X_AXIS'] = 0
        self.movements['Y_AXIS'] = 0
        self.movements['Z_AXIS'] = 0
        self.movements['WRIST_PITCH'] = 0
        self.movements['WRIST_ROLL'] = 0
        self.movements['GRIP'] = 0

        if data.buttons[self.HALF_SPEED_BTN]:
            self.MULTIPLIER = 0.5
        elif data.buttons[self.NORM_SPEED_BTN]:
            self.MULTIPLIER = 1.0
        elif data.buttons[self.ONEPFIVE_SPEED_BTN]:
            self.MULTIPLIER = 1.5
        elif data.buttons[self.DOUBLE_SPEED_BTN]:
            self.MULTIPLIER = 2.0
        rospy.loginfo("Speed toggled to: "+str(self.MULTIPLIER)+"%")

        # Main axes:
        # Big stick forward/backward
        if (abs(data.axes[self.X_AXIS]) >= self.DEADBAND):
            self.movements['X_AXIS'] = data.axes[self.X_AXIS] / 5.0 * self.MULTIPLIER
        # Big stick side-to-side
        if (abs(data.axes[self.Y_AXIS]) >= self.DEADBAND):
            self.movements['Y_AXIS'] = data.axes[self.Y_AXIS] / 5.0 * self.MULTIPLIER
        # Dial up/down
        if (abs(data.axes[self.Z_AXIS]) >= self.DEADBAND):
            self.movements['Z_AXIS'] = data.axes[self.Z_AXIS] / 5.0 * self.MULTIPLIER

        # Wrist
        # Small joy up/down
        if (abs(data.axes[self.WRIST_PITCH]) >= self.DEADBAND):
            self.movements['WRIST_PITCH'] = data.axes[self.WRIST_PITCH] / 2.0 * self.MULTIPLIER
        # Small joy side-to-side
        if (abs(data.axes[self.WRIST_ROLL]) >= self.DEADBAND):
            self.movements['WRIST_ROLL'] = data.axes[self.WRIST_ROLL] / 2.0 * self.MULTIPLIER

        # End-effector
        # Front trigger: close
        if data.buttons[self.EE_CLOSE_BTN]:
            self.movements['GRIP'] = 1
        # Thumb trigger: open
        if data.buttons[self.EE_OPEN_BTN]:
            self.movements['GRIP'] = -1

        # MOVE ARM
        self.write_serial()

if __name__ == '__main__':
    rospy.init_node("IK_arm_controls")
    rospy.loginfo("IK_arm_controls node started")
    controller = IKController()
    rospy.spin()