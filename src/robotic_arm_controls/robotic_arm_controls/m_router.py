#!/usr/bin/python3

import os
import signal
import threading
from typing import TypeVar # For parameter helper function
import serial
import time

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String # msg used by publisher and subscriber


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

        #Parameters
        self.RETRY_DELAY = self.get_param("timeout_delay", rclpy.Parameter.Type.DOUBLE, 0.1)  # time (s) to attempt serial connection
        self.serial_device = self.get_param("serial_dev", rclpy.Parameter.Type.STRING, "/dev/arm_mega")
        self.baudrate = self.get_param("baudrate", rclpy.Parameter.Type.INTEGER, 1000000)
        self.read_enabled = self.get_param("read_enable", rclpy.Parameter.Type.BOOL, True) # boolean for arduino feedback status

        #Serial connection
        self.connect_serial()

        #Threading
        if self.read_enabled:
            self.run = True # flag to stop the read thread

            self.readThread = threading.Thread(target=self.read_loop)
            self.readThread.start()

            signal.signal(signal.SIGINT, self.signal_handler)

        # Initialising variables
        self.movement = ""


    ### Serial Communication ###    
    """
    Connects to arduino over serial; used on startup, timeouts or can be manually done
    signal_num represents the signal that triggered the function
    frame represents the stack frame when the signal was triggered
    """
    def connect_serial(self) -> None:
        self.get_logger().info("Connecting to serial")
        time.sleep(1)

        self.connecting = True  

        while self.connecting:
            time.sleep(self.RETRY_DELAY)
            try:
                self.get_logger().info("Establishing serial connection...")
                self.ARDUINO = serial.Serial(port=self.serial_device, baudrate=self.baudrate, timeout=self.RETRY_DELAY)
                
                self.get_logger().info("Connection to serial established:")
                self.connecting = False

            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connecting = True

    """
    Reading done on a seaparate thread to not block and to ensure that all messages are read
    """
    def read_loop(self) -> None:
        self.get_logger().info("Running serial reader thread...")
    
        while self.run:
            try:
                if not self.connecting and self.ARDUINO.in_waiting:
                    
                    byte_chunk = self.ARDUINO.read_until(b'!')
                        
                    #self.tp_executor.submit(self.publishMessage, byte_chunk[:-1])
                    self.get_logger().info(byte_chunk[:-1])
            except:
                self.get_logger().error("Could not publish message even while connected!")
                self.run = False

        # sends kill signal to the read process
        self.get_logger().info("Killing the read thread")
        os.kill(os.getpid(), 9)

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
        self.movement = message
        self.write_serial()

    """
    Passes messages to the arduino over serial
    """
    def write_serial(self) -> None:
        if not self.connecting:
            try:
                self.ARDUINO.write(bytes(self.movement,'utf-8'))
                self.get_logger().info(f"Movement msg to serial: {self.movement}")

            except:
                self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
                self.connecting = True


    ### Signal Handling ###   
    """
    Handler for when ctrl+c is pressed
    Stops the read thread, ensuring that the node can be terminated cleanly
    """
    def signal_handler(self, signal_num, frame):
        self.get_logger().info("Signal handler called")
        self.run = False


    ### Parameter Helper Function ###
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


### MAIN ###
def main(args=None):
    rclpy.init(args=args) # if any args specified on node startup (via ros2 run <package> <node> args...)
    
    router_node = Router() # class above
    
    # Spinning the node with a small delay in between allows the SIGINT signal to be caught and handled by the signal handler we declared
    # Tried multithreaded executors as well but they didn't lead to clean termination of the node
    while rclpy.ok():
        rclpy.spin_once(router_node, timeout_sec=0.0001)

    router_node.destroy_node()
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise

if __name__ == "__main__":
    main()
