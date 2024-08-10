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
        self.cmd_subscriber = self.create_subscription(String, "/arm_cmd", self.cmd_callback_function, 20)

        #Publishers
        self.state_publisher = self.create_publisher(ArmPose, '/arm_feedback', 20)
        self.error_publisher = self.create_publisher(ArmError, '/arm_faults', 20)
        
        #Parameters
        self.RETRY_DELAY = self.get_param("timeout_delay", rclpy.Parameter.Type.DOUBLE, 0.1)  # time (s) to attempt serial connection
        self.serial_device = self.get_param("serial_dev", rclpy.Parameter.Type.STRING)
        self.baudrate = self.get_param("baudrate", rclpy.Parameter.Type.INTEGER, 500000)

        #Threading
        #self.pool_executor = Pool()
        self.run = True
        self.tp_executor = ThreadPoolExecutor(max_workers=5) #creating 3 threads
        self.reader = self.tp_executor.submit(self.read_loop)
        # whether to connect or not; reconnector will then try to establish a serial conn.
        self.connecting = True  
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
            if self.connecting:
                time.sleep(self.RETRY_DELAY)
                try:
                    self.get_logger().info("Establishing serial connection...")
                    self.ARDUINO = serial.Serial(port=self.serial_device, baudrate=self.baudrate, timeout=self.RETRY_DELAY)
                    
                    self.get_logger().info("Connection to serial established:")
                    self.connecting = False

                except:
                    self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                    self.connecting = True

        # sends kill signal to the read process
        os.kill(os.getpid(), 9)

    """
    Reading done on a seaparate thread to not block main
    """
    def read_loop(self):
        self.get_logger().info("Running serial reader thread...")
        #time.sleep(1)
    
        while self.run:
            try:
                if not self.connecting and self.ARDUINO.in_waiting:
                    
                    byte_chunk = self.ARDUINO.read_until(b'!')
                        
                    #self.tp_executor.submit(self.publishMessage, byte_chunk[:-1])
                    #self.get_logger().info(byte_chunk[:-1])
            except:
                self.get_logger().info("Could not publish message even while connected!")
                self.get_logger().info("Will attempt to reconnect")
                self.connecting = True

        # sends kill signal to the read process
        os.kill(os.getpid(), 9)

    """
    Executes derived movement from the Joy (usually "/joy") topic
    """
    def write_serial(self):
        if not self.connecting:
            try:
                self.ARDUINO.write(bytes(self.movement,'utf-8'))
                self.get_logger().info(f"Movement msg to serial: {self.movement}")

            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connecting = True

    """
    Sends stop command to arduino and tries to reconnect if the connection is lost
    """
    def force_stop(self):
        if not self.connecting:
            try:
                self.ARDUINO.write(bytes("stop;!",'utf-8'))
                self.get_logger().info("Movement msg to serial: stop;!")
            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connecting = True # connect flag true -> connector will try to establish a connection

    """
    Sends serial messages to the arduino based on messages recieved from the Manual node
    """
    def cmd_callback_function(self, message: String) -> None:
        
        string_message = message.data
        self.publishToArduino(string_message)


    """
    Helper method to publish messages to the arduino over serial
    Only publishes if the message is different from the last message sent
    """
    def publishToArduino(self, message) -> None:
        if (message != self.movement):
            self.movement = message
            self.write_serial()
        
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

    # For some weird reason, raising an error in try makes it
    # so that the node shuts down properly on Ctrl-C
    try:
        rclpy.spin(router_node) # spin = debounce (run for as long as it's on)
    except KeyboardInterrupt:
        print("Spin interrupted by user (Ctrl+C)")

    router_node.destroy_node()
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise
    



if __name__ == "__main__":
    main()