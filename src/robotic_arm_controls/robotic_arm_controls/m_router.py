#!/usr/bin/python3

import os
import signal
import threading
from typing import TypeVar # For parameter helper function
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool

import serial

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from std_msgs.msg import String # msg used by publisher and subscriber
from general_interfaces.msg import ArmPose, ArmError, ToggleMessage
import time

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

class Router(Node):

    def __init__(self, node_name: str = "router"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        #Subscribers
        sub_callback_group = MutuallyExclusiveCallbackGroup()

        self.m_subscriber = self.create_subscription(ToggleMessage, "/manual_states", self.mn_callback_function, qos_profile = 20, callback_group = sub_callback_group)
        self.ik_subscriber = self.create_subscription(ArmPose, "/goal_states", self.ik_callback_function, qos_profile = 20, callback_group = sub_callback_group)
        self.mode_subscriber = self.create_subscription(String, "/mode", self.mode_callback_function, qos_profile = 20, callback_group = sub_callback_group)

        #Publishers
        self.state_publisher = self.create_publisher(ArmPose, '/arm_feedback', 20)
        self.error_publisher = self.create_publisher(ArmError, '/arm_faults', 20)
        
        #Parameters
        self.RETRY_DELAY = self.get_param("timeout_delay", rclpy.Parameter.Type.DOUBLE, 0.1)  # time (s) to attempt serial connection
        self.serial_device = self.get_param("serial_dev", rclpy.Parameter.Type.STRING)
        self.baudrate = self.get_param("baudrate", rclpy.Parameter.Type.INTEGER, 115200)

        #Threading
        #self.pool_executor = Pool()
        self.run = True
        self.tp_executor = ThreadPoolExecutor(max_workers=5) #creating 3 threads
        #reading from serial will be done in one thread
        self.reader = self.tp_executor.submit(self.read_loop) 
        
        # whether to connect or not; reconnector will then try to establish a serial conn.
        self.connect = True  
        # connection to serial will be handled by this thread
        self.reconnector = self.tp_executor.submit(self.connect_serial) 

        # Initialising variables
        self.movement = ""
        self.feedback_available = False  # boolean for arduino feedback status

    # Serial communication methods
    """
    Connects to arduino over serial; used on startup, timeouts or can be manually done
    signal_num represents the signal that triggered the function
    frame represents the stack frame when the signal was triggered
    """
    def connect_serial(self):
        self.get_logger().info("Running serial connector thread...")
        time.sleep(1)
    
        while self.run:
            if self.connect:
                time.sleep(self.RETRY_DELAY)
                try:
                    self.get_logger().info("Establishing serial connection...")
                    self.ARDUINO = serial.Serial(port=self.serial_device, baudrate=self.baudrate, timeout=self.RETRY_DELAY)
                    
                    self.get_logger().info("Connection to serial established:")
                    self.connect = True

                except:
                    self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")

        # sends kill signal to the read process
        os.kill(os.getpid(), 9)

    """
    Reader thread loop running read_serial as long as run
    Publishes the ArmState to the /arm_feedback topic
    """
    def read_loop(self):
        self.get_logger().info("Running serial read loop thread...")
        time.sleep(1) # delay upon start of this thread
        
        while self.run:

            #self.get_logger().info(str(self.connect))
            #self.get_logger().info(str(self.ARDUINO.in_waiting))
            if not self.connect and self.ARDUINO.in_waiting:
                
                byte_chunk = self.ARDUINO.read_until(b'!')
                
                self.tp_executor.submit(self.publishMessage, byte_chunk[:-1])
                self.get_logger().info(byte_chunk)

        # sends kill signal to the read process
        os.kill(os.getpid(), 9)

    """
    Executes derived movement from the Joy (usually "/joy") topic
    """
    def write_serial(self):
        if not self.connect:
            try:
                self.ARDUINO.write(bytes(self.movement,'utf-8'))
                self.get_logger().info(f"Movement msg to serial: {self.movement}")

            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connect = True

    """
    Sends stop command to arduino and tries to reconnect if the connection is lost
    """
    def force_stop(self):
        if not self.connect:
            try:
                self.ARDUINO.write(bytes("stop;!",'utf-8'))
                self.get_logger().info("Movement msg to serial: stop;!")
            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connect = True # connect flag true -> connector will try to establish a connection

    """
    Checks whether threads are alive, revives them if they're not
    """
    def check_threads(self):
        if (self.reader.done()):
            self.get_logger().info("Reader thread is dead, restarting...")
            self.reader = self.tp_executor.submit(self.read_loop)

        if (self.reconnector.done()):
            self.get_logger().info("Reconnector thread is dead, restarting...")
            self.reconnector = self.tp_executor.submit(self.connect_serial)
        
        '''
        if (self.publisher.done()):
            self.get_logger().info("Publisher thread is dead, restarting...")
            self.publisher = self.tp_executor.submit(self.publishing_loop)
            '''

    """
    This method takes the decoded string and builds the ArmState message, returns message to be published
    """
    def build_arm_pose_message(self, string_message):
        #self.get_logger().info(string_message[2:])
        state_values = string_message.split(";") # Split string into array using ';' as the delimiter

        if (len(state_values) != 8):
            self.get_logger().warn("Invalid feedback message")
            return None
        
        # positions: 4 wide array of float
        # 0: angle to execute of tower in rad
        # 1: extension la1 in inches from 0 to 6
        # 2: extension of la2 in inches
        # 3: pitch of wrist in radians
        
        positions = [0.0, 0.0, 0.0, 0.0]

        for i in range(4):
            positions[i] = round(float(state_values[i+1]),3)
        
        #self.get_logger().info(f"{positions[0]}, {positions[1]}, {positions[2]}, {positions[3]}")

        message_to_send = ArmPose()
        message_to_send.positions = positions

        return message_to_send


    # Callbacks
    """
    Sends serial messages to the arduino based on messages recieved from the IK node
    """
    def ik_callback_function(self, message: ArmPose) -> None:
        positions = message.positions

        string_message = f"S;{round(positions[0],3)};{round(positions[1],3)};{round(positions[2],3)};{round(positions[3],3)};!"
        
        self.publishToArduino(string_message)
    
    """
    Sends serial messages to the arduino based on messages recieved from the Manual node
    """
    def mn_callback_function(self, message: ToggleMessage) -> None:
        string_message = f"S;{message.tw};{message.la1};{message.la2};{message.wr_pitch};{message.wr_roll};{message.ee};!"
        
        self.publishToArduino(string_message)

    """
    Sends serial messages to the arduino based on messages recieved from the IK node
    """
    def mode_callback_function(self, message: String) -> None:
        self.publishToArduino(str(message.data))

    """
    Helper method to publish messages to the arduino over serial
    Only publishes if the message is different from the last message sent
    """
    def publishToArduino(self, message) -> None:
        if (message != self.movement):
            self.movement = message
            self.write_serial()

    """
    Thread loop for publishing arduino messages to the /arm_feedback topic
    """
    def publishMessage(self, byte_chunk):
        
        string_message = str(byte_chunk, 'UTF-8')
        
        if "f" in string_message:
            #self.get_logger().info("Publishing arm state")
            state_values = string_message.split(";") # Split string into array using ';' as the delimiter

            if (len(state_values) != 8):
                self.get_logger().warn("Invalid feedback message")
                return None
            
            # positions: 4 wide array of float
            # 0: angle to execute of tower in rad
            # 1: extension la1 in inches from 0 to 6
            # 2: extension of la2 in inches
            # 3: pitch of wrist in radians
            
            positions = [0.0, 0.0, 0.0, 0.0]

            for i in range(4):
                positions[i] = float(state_values[i+1])
            
            #self.get_logger().info(f"{positions[0]}, {positions[1]}, {positions[2]}, {positions[3]}")

            message_to_send = ArmPose()
            message_to_send.positions = positions
            
            if (message_to_send != None):
                self.state_publisher.publish(message_to_send)
        
    """
    Helper function to declare and get the value of a ROS launch parameter,
    including support for default values.
    """
    def get_param(
        self,
        param_name: str,
        param_type: rclpy.Parameter.Type,
        default_val: T | None = None,
        logging: bool = True,
    ) -> T:

        self.declare_parameter(param_name, param_type)

        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = Parameter(param_name, param_type, default_val)
            param_val = self.get_parameter_or(param_name, default_param).value

        assert param_val is not None, "The parameter received was None."

        if logging:
            self.get_logger().info(f"Using {param_name}: {param_val}")

        return param_val


def main(args=None):
    rclpy.init(args=args) # if any args specified on node startup (via ros2 run <package> <node> args...)
    
    '''
    rclpy.spin(router_node) # spin = debounce (run for as long as it's on)
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise
    '''
    router_node = Router() # class above

    executor = MultiThreadedExecutor()  # for multiple threads

    # For some weird reason, raising an error in try makes it
    # so that the node shuts down properly on Ctrl-C
    try:
        raise ValueError("Ignore this message")
    except KeyboardInterrupt:
        print("Spin interrupted by user (Ctrl+C)")
    
    rclpy.spin(router_node, executor = executor) # spin = debounce (run for as long as it's on)


    router_node.destroy_node()
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise

if __name__ == "__main__":
    main()