#!/usr/bin/python

import rospy

#Import msg types for publishers & subscribers
from sensor_msgs.msg import Joy
from std_msgs.msg import String


class ArmJoystickController:
    def __init__(self):
        self.arm_control = ""

        #Toggle buttons
        self.speed_toggle = 0
        self.actuator_toggle = 0

        #Publishers
        self.arm_control_pub = rospy.Publisher("/arm_control", String, queue_size=1000)

        #Subscribers
        self.joy_sub = rospy.Subscriber("/joy", Joy, self.joy_callback)

    #Callback for manual; TODO: define another for inv. kinematics
    def joy_callback(self, joy_msg):
        #Recall /joy contains axes[] & buttons[]
        axes = joy_msg.axes
        buttons = joy_msg.buttons
        
        #Axes
        ACTUATOR = axes[1]
        TOWER = axes[2]
        SPEED = axes[3]
        WRIST_ROLL = axes[4]
        WRIST_PITCH = axes[5]

        #Buttons
        EE_CLOSE_BUTTON = buttons[0]
        EE_OPEN_BUTTON = buttons[1]

        #Toggle buttons
        SPEED_TOGGLE_BUTTON = buttons[10]
        ACTUATOR_TOGGLE_BUTTON = buttons[11]

        #Defaults
        THRESHOLD = 0.2     #to recognize axis movement
        ROUND_PRECISION = 3 #decimal places for all decimal values

        #Speed-related
        SPEED = 0
        SPEED_MULTIPLIER = 0.0
        SPEED_THRESHOLD = 0.05

        #Map: [-1.0, 1.0] -> [0.0, 2.0]
        if axes[3] < 0:
            SPEED = 1 - round(abs(axes[3]), ROUND_PRECISION)
        else:
            SPEED = 1 + round(axes[3], ROUND_PRECISION)

        #Mechanisms for toggle buttons
        #50-100% speed cap toggle
        #0: 100% of max: arm, 1: 50%: forearm
        if SPEED_TOGGLE_BUTTON == 1 :
            if self.speed_toggle == 0:
                self.speed_toggle = 1
                rospy.loginfo("Speed toggled to 50% max")
            else:
                self.speed_toggle = 0
                rospy.loginfo("Speed toggled to 100% max")

        if self.speed_toggle == 0:
            SPEED_MULTIPLIER = 1.0
        else:
            SPEED_MULTIPLIER = 0.5#50%
        SPEED = SPEED*SPEED_MULTIPLIER

        #L-actuator toggle
        #0: L1: arm, 1: L2: forearm
        if ACTUATOR_TOGGLE_BUTTON == 1 :
            if self.actuator_toggle == 0:
                self.actuator_toggle = 1
                rospy.loginfo("Actuator toggled to L2")
            else:
                self.actuator_toggle = 0
                rospy.loginfo("Actuator toggled to L1")

        #All programmed axes <= Threshold & no programed buttons pressed, so we send the stop cmd
        axes_areStationary = (abs(ACTUATOR) <= THRESHOLD) & (abs(TOWER) <= THRESHOLD) & (abs(WRIST_ROLL) <= THRESHOLD) & (abs(WRIST_PITCH) <= THRESHOLD)
        buttons_notPressed = (SPEED_TOGGLE_BUTTON == 0) & (ACTUATOR_TOGGLE_BUTTON == 0) & (EE_CLOSE_BUTTON == 0) & (EE_OPEN_BUTTON == 0)
        if axes_areStationary & buttons_notPressed:
            self.arm_control = "stop"
            self.arm_control_pub.publish(self.arm_control)
            rospy.loginfo("Sending arm control msg: "+self.arm_control)
        
        elif SPEED > SPEED_THRESHOLD:

            #Will store the joy value of whichever arm part
            #Represents the direction we want to move
            PART_VALUE = 0.0

            self.arm_control = ""

            #Arm & forearm
            if abs(ACTUATOR) >= THRESHOLD:
                if self.actuator_toggle  == 1:
                    self.arm_control = "forearm_angle;"
                else:
                    self.arm_control = "arm_angle;"
                PART_VALUE = ACTUATOR
                self.arm_control += str(round(PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)

            #Tower
            if abs(TOWER) >= THRESHOLD:
                self.arm_control = "tower_rotation;"
                PART_VALUE = TOWER
                self.arm_control += str(round(-1.0*PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)

            #Wrist
            if abs(WRIST_ROLL) >= THRESHOLD:
                self.arm_control = "wrist_roll;"
                PART_VALUE = WRIST_ROLL
                self.arm_control += str(round(PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)

            #Wrist
            if abs(WRIST_PITCH) >= THRESHOLD:
                self.arm_control = "wrist_pitch;"
                PART_VALUE = WRIST_PITCH
                self.arm_control += str(round(PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)

            #End effector
            if EE_OPEN_BUTTON == 1 and EE_CLOSE_BUTTON == 0:
                self.arm_control = "claw_angle;"
                PART_VALUE = 1.0
                self.arm_control += str(round(PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)

            elif EE_OPEN_BUTTON == 0 and EE_CLOSE_BUTTON == 1:
                self.arm_control = "claw_angle;"
                PART_VALUE = -1.0
                self.arm_control += str(round(PART_VALUE, ROUND_PRECISION))+";"+str(SPEED)
                self.arm_control_pub.publish(self.arm_control)
                rospy.loginfo("Sending arm control msg: "+self.arm_control)



if __name__ == '__main__':
    rospy.init_node("arm_joystick_controller")
    rospy.loginfo("arm_joystick_controller node started")
    controller = ArmJoystickController()
    rospy.spin()
