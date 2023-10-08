#!/usr/bin/python

# Imports
import rospy
import serial
import time
import signal
import threading
import sys
import os
from concurrent.futures import ThreadPoolExecutor

# Import msg types for publishers & subscribers
from sensor_msgs.msg import Joy
from std_msgs.msg import String
from std_msgs.msg import Bool

class MArmController:

    def __init__(self):

        # Stores message to serial
        self.movement = ""

        # Record previous cmds so as to not repeat them
        self.partsInMotion = ["stop;!"]

        # Default Constants
        self.DEADBAND = rospy.get_param('~deadband', 0.35) # to recognize as axial movement
        self.ROUND_PRECISION = 3

        # Speed-related
        self.SPEED = 1.0
        self.MULTIPLIER = 1.0
        self.SPEED_DEADBAND = 0.05
        self.MOTOR_CAP = 1000
        self.ACTUATOR_CAP = rospy.get_param('~actuator_cap', 600)

        # Axes indices
        self.ACTUATOR = 1
        self.TOWER = 2
        self.SPEED_AXIS = 3
        self.WRIST_ROLL = 4
        self.WRIST_PITCH = 5

        # Buttons indices
        self.EE_CLOSE_BUTTON = 0
        self.EE_OPEN_BUTTON = 1

        # Toggle buttons
        self.LOWEST_SPEED_BTN = 4 # 0.25x
        self.SECOND_SPEED_BTN = 2 # 0.5x
        self.THIRD_SPEED_BTN = 3  # 0.75x
        self.NORM_SPEED_BTN = 5   # 1x
        self.FORCE_STOP_BUTTON = 6
        self.ACTUATOR_HOLD_BUTTON = 11

        # Unused buttons
        self.B1 = 10
        self.B2 = 7
        self.B3 = 8
        self.B4 = 9

        # Joy subscriber
        self.JOY_SUB = rospy.Subscriber("/arm_joy", Joy, self.joy_callback)

        # Serial connection
        self.startup = True # if true, next connection will send the stop cmd at a delay of 1s, else 0.001s
        self.connecting = True # boolean for connection status
        self.RETRY_DELAY = rospy.get_param('~timeout_delay', 0.1) # time (s) to attempt serial connection

        # Using signal lib for timeout mechanism
        signal.signal(signal.SIGALRM, self.connect_serial) # when SIGALRM triggers, run self.connect_serial
        signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0) # manually SIGARLM to start serial connection

        signal.signal(signal.SIGINT, self.graceful_shutdown)
        self.run = True # threads will stop running if false
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.reader = self.executor.submit(self.read_loop)

    # Connects to serial; used on startup, timeouts or can be manually done ()
    def connect_serial(self, signum, frame):
        try:
            self.connecting = True
            rospy.loginfo("Establishing serial connection...")
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
            self.ARDUINO = serial.Serial(port=rospy.get_param("~serial_dev"),
                                               baudrate = rospy.get_param('~baudrate', 115200),
                                               timeout  = self.RETRY_DELAY,
                                               parity   = serial.PARITY_NONE,
                                               stopbits = serial.STOPBITS_ONE,
                                               bytesize = serial.EIGHTBITS)
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            rospy.loginfo("Connection to serial established")
            if not self.startup:
                timer = threading.Timer(0.001, self.force_stop)
            else:
                timer = threading.Timer(1, self.force_stop)
                self.startup = False
            timer.start()
        except:
            rospy.loginfo("Connection Error: serial failed, trying every "+str(self.RETRY_DELAY)+"s")
            self.connecting = True
            self.connect_serial

    # Emergency stop
    def force_stop(self):
        try:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
            #self.ARDUINO.write("stop;!")
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

            rospy.loginfo("Movement msg to serial: stop;!")
            self.connecting = False
        except:
            rospy.loginfo("Connection Error: serial failed, trying every "+str(self.RETRY_DELAY)+"s")
            self.connecting = True
            self.connect_serial

    # Tell threads to shutdown
    def graceful_shutdown(self, sig, frame):
        rospy.loginfo("Terminating all threads...")
        self.run = False
        self.executor.shutdown()
        rospy.loginfo("Shutting node down...")
        raise SystemExit

    # Reader thread loop running read_serial as long as self.run
    def read_loop(self):
        while self.run:
            if not self.connecting and self.ARDUINO.in_waiting:
                byte_chunk = self.ARDUINO.read_until('!')
                rospy.loginfo(byte_chunk[:-1])
        #os.kill(os.getpid(), 9)
    
    # Reads all characters on the serial port and returns them
    def read_serial(self):
        read_buffer = b''
        while not self.connecting:
            byte_chunk = self.ARDUINO.read_until('!')
            break
        return byte_chunk[:-1] # slice last delimiter byte

    # Executes derived movement from "/joy" topic
    def write_serial(self):
        if (not self.connecting and self.ARDUINO.writable()):
            try:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
                self.ARDUINO.write(self.movement)
                rospy.loginfo("Movement msg to serial: "+self.movement)
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
            except:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
                rospy.loginfo("Connection Error: could not write serial")
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
        else:
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

    # Main loop for joy msg processing
    def joy_callback(self, data):
        if data.buttons[self.FORCE_STOP_BUTTON] and data.buttons[self.ACTUATOR_HOLD_BUTTON]:
            self.startup = True
            rospy.loginfo("Forcing serial reconnection")
            signal.setitimer(signal.ITIMER_REAL, 0.001, 0)
            time.sleep(1)
        elif not self.connecting:

            # Map: [-1.0, 1.0] -> [0.0, 2.0]
            if data.axes[self.SPEED_AXIS] < 0:
                self.SPEED = 1 - round(abs(data.axes[self.SPEED_AXIS]), self.ROUND_PRECISION)
            else:
                self.SPEED = 1 + round(data.axes[self.SPEED_AXIS], self.ROUND_PRECISION)
            self.SPEED /= 2
            
            # Speed toggles, 50%, 100%, 150% & 200%
            if data.buttons[self.LOWEST_SPEED_BTN] and self.MULTIPLIER != 0.25:
                self.MULTIPLIER = 0.25
                rospy.loginfo("Speed multiplier changed to 25%")
            elif data.buttons[self.SECOND_SPEED_BTN]and self.MULTIPLIER != 0.5:
                self.MULTIPLIER = 0.5
                rospy.loginfo("Speed multiplier changed to 50%")
            elif data.buttons[self.THIRD_SPEED_BTN]and self.MULTIPLIER != 0.75:
                self.MULTIPLIER = 0.75
                rospy.loginfo("Speed multiplier changed to 75%")
            elif data.buttons[self.NORM_SPEED_BTN]and self.MULTIPLIER != 1.0:
                self.MULTIPLIER = 1.0
                rospy.loginfo("Speed multiplier changed to 100%")
            
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
            stop_condition = (axes_stationary and buttons_unpressed) or (self.SPEED <= self.SPEED_DEADBAND)
            if ((self.partsInMotion[-1] != "stop;!") & stop_condition) or (axes_stationary and data.buttons[self.FORCE_STOP_BUTTON]):
                self.partsInMotion = ["stop;!"]
                self.movement = "stop;!"
                self.write_serial()
            
            # At least an axis or button pressed while speed > speed threshold
            elif self.SPEED > self.SPEED_DEADBAND:

                self.SPEED *= self.MULTIPLIER
                tmp_speed = int(self.ACTUATOR_CAP*self.SPEED)
                
                # Arm & forearm
                tmp_axis = data.axes[self.ACTUATOR]
                if abs(tmp_axis) > self.DEADBAND:
                    if data.buttons[self.ACTUATOR_HOLD_BUTTON]:
                        self.movement = "L1;"
                    else:
                        self.movement = "L2;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        if tmp_speed < 105: # no movement, but current observed; waste of power
                            self.movement += str(105)+";!"
                        else:
                            self.movement += str(int(tmp_speed))+";!"
                        self.write_serial()

                self.SPEED *= self.MOTOR_CAP     # All below parts have motor cap
                tmp_speed = int(self.SPEED) >> 1 # WR has ~1/2 speed mult.; equiv to >> 1

                # Wrist Roll
                tmp_axis = data.axes[self.WRIST_ROLL]
                if abs(tmp_axis) > self.DEADBAND:
                    self.movement = "WR;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "1;"
                        else:
                            self.movement += "-1;"
                        self.movement += str(int(tmp_speed))+";!"
                        self.write_serial()

                # WP & EE have ~1/4 speed multiplier; equiv to >> 2
                tmp_speed >>= 1
                tmp_str = str(int(tmp_speed))+";!"

                # Wrist Pitch
                tmp_axis = data.axes[self.WRIST_PITCH]
                if abs(tmp_axis) > self.DEADBAND:
                    self.movement = "WP;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "1;"
                        else:
                            self.movement += "-1;"
                        self.movement += tmp_str
                        self.write_serial()
                
                # End effector
                if data.buttons[self.EE_OPEN_BUTTON] ^ data.buttons[self.EE_CLOSE_BUTTON]:
                    self.movement = "EE;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if data.buttons[self.EE_OPEN_BUTTON]:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        self.movement += tmp_str
                        self.write_serial()

                # Tower
                tmp_axis = data.axes[self.TOWER]
                if abs(tmp_axis) > self.DEADBAND:
                    self.movement = "TW;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        self.movement += str(int(tmp_speed >> 1))+";!"
                        self.write_serial()

if __name__ == '__main__':
    rospy.init_node("M_arm_controls")
    rospy.loginfo("M_arm_controls node started")
    controller = MArmController()
    rospy.spin()