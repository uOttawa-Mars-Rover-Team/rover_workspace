#!/usr/bin/python

import rospy
import serial
import time

#Import msg types for publishers & subscribers
from std_msgs.msg import String


class ArmControl:
    def __init__(self):
        #Serial to arduino
        self.movement = ""

        #Record previous cmd so we don't repeat it
        self.previousData = ""

        #Serial configurations
        #self.arduino = serial.Serial(port='/dev/ttyACM0', baudrate=9600, timeout=.1)
        baudrate = rospy.get_param('~baudrate', 115200)
        self.arduino = serial.Serial(baudrate=baudrate)
        self.arduino.port = rospy.get_param("~serial_dev")
        self.arduino.open()

        #Publishers
        #self.position_pub = rospy.Publisher("/arm_position", String, queue_size=10)
        #not implemented yet; same format as arm control msg

        #Subscribers
        self.arm_control_sub = rospy.Subscriber("/arm_control", String, self.arm_joy_callback)


    #Executes derived movement from "/arm_controls" topic
    def write_serial(self):
        self.arduino.write(self.movement)
        time.sleep(0.6)


    def arm_joy_callback(self, arm_control_msg):

        #Recall /arm_controls is of the form 'ARM_PART:DIRECTION:SPEED'
        msg_parts = arm_control_msg.data.split(";")

        #See above
        part = msg_parts[0]
        if msg_parts[0] == "stop":
            self.movement = "stop;"
        else:
            #-1: Right or backward, 1: Left or forward
            direction = 0
            if float(msg_parts[1]) < 0:
                direction = -1
            else:
                direction = 1

            #Between 0.0 to 2.0
            speed = float(msg_parts[2])
            
            #Speed limit for most parts; 255 for L1, L2
            MOTOR_SPEED_CAP = 1000
            ACTUATOR_SPEED_CAP = 255

            currentCap = ""
            if part == "tower_rotation":
                self.movement = "TW;"
                currentCap = MOTOR_SPEED_CAP

            elif part == "arm_angle":
                self.movement = "L1;"
                currentCap = ACTUATOR_SPEED_CAP

            elif part == "forearm_angle":
                self.movement = "L2;"
                currentCap = ACTUATOR_SPEED_CAP

            elif part == "wrist_roll":
                self.movement = "WR;"
                currentCap = MOTOR_SPEED_CAP

            elif part == "wrist_pitch":
                self.movement = "WP;"
                currentCap = MOTOR_SPEED_CAP

            elif part == "claw_angle":
                self.movement = "EE;"
                currentCap = MOTOR_SPEED_CAP
            
            
            self.movement += str(direction) + ";" + str(int(speed*currentCap)/2) + ";"

        #Send stop only if previous wasnt stop cmd
        stop_condition = (self.movement == "stop;") & (str(self.previousData) != "stop;!")
        #Send non-'stop' cmd only if previous cmd is stop;
        other_cmd_condition = (self.movement != "stop;") & (str(self.previousData) == "stop;!")
        if stop_condition | other_cmd_condition:
            #Delimiter for arduino code
            self.movement = self.movement+"!"

            #Current cmd is the new previous cmd
            self.previousData = self.movement

            rospy.loginfo("Movement msg to serial: "+self.movement)
            self.write_serial()


if __name__ == '__main__':
    rospy.init_node("arm_control")
    rospy.loginfo("arm_control node started")
    controller = ArmControl()
    rospy.spin()