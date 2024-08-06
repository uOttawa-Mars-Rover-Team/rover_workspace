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
from rclpy.action import ActionServer, CancelResponse
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from std_msgs.msg import String # msg used by publisher and subscriber
from general_interfaces.msg import ArmPose, ArmError, ToggleMessage
from general_interfaces.action import ZeroArm
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
        
        #Action Servers
        self.zero_server = ActionServer(self, ZeroArm, 'zero_arm', callback_group = ReentrantCallbackGroup(), execute_callback = self.zero_execute_callback, cancel_callback = self.zero_cancel_callback)
        
        #Parameters
        self.RETRY_DELAY = self.get_param("timeout_delay", rclpy.Parameter.Type.DOUBLE, 0.1)  # time (s) to attempt serial connection
        self.serial_device = self.get_param("serial_dev", rclpy.Parameter.Type.STRING)
        self.baudrate = self.get_param("baudrate", rclpy.Parameter.Type.INTEGER, 115200)

        #Threading
        #self.pool_executor = Pool()
        self.run = True  # threads will stop running if false
        self.tp_executor = ThreadPoolExecutor(max_workers=5) #creating 3 threads
        self.reader = self.tp_executor.submit(self.read_loop) #reading from serial will be done in one thread
        #self.publisher = self.tp_executor.submit(self.publishing_loop) #publishing to serial will be done in another thread

        # Initialising variables
        self.movement = ""
        self.zeroing = False
        self.startup = True  # if true, next connection will send the stop cmd at a delay of 1s, else 0.001s
        self.connecting = True  # boolean for connection status
        self.feedback_available = False  # boolean for arduino feedback status

        # Graceful shutdown of the code when the interrupt signal is recieved (ctrl+c)
        signal.signal(signal.SIGINT, self.graceful_shutdown)

        #Signals for serial connection
        # when SIGALRM triggers, run self.connect_serial
        signal.signal(signal.SIGALRM, self.connect_serial)  
        # once itimer expires, SIGALRM is triggered and connect_serial is run
        signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

        time.sleep(0.5)


    # Serial communication methods
    """
    Connects to arduino over serial; used on startup, timeouts or can be manually done
    signal_num represents the signal that triggered the function
    frame represents the stack frame when the signal was triggered
    """
    def connect_serial(self, signal_num, frame) -> None:
        
        self.get_logger().info("OHHHHEYAAA?")
        try:
            self.connecting = True
            self.get_logger().info("Establishing serial connection...")
            
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

            self.ARDUINO = serial.Serial(
                port=self.serial_device,
                baudrate=self.baudrate,
                timeout=self.RETRY_DELAY,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )

            signal.setitimer(signal.ITIMER_REAL, 0, 0) #this resets the timer
            self.get_logger().info("Connection to serial established:")
            
            if not self.startup:
                # if not starting up we can immediately send a stop command
                timer = threading.Timer(0.001, self.force_stop)
            else:
                # if starting up, we must wait for the arduino to fully boot up before sending a stop command
                timer = threading.Timer(1, self.force_stop)
                self.startup = False
            
            timer.start()
        
        except:
            self.get_logger().warn(f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s")
            self.connecting = True
            self.connect_serial

    """
    Sends stop command to arduino and tries to reconnect if the connection is lost
    """
    def force_stop(self):
        try:
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
            self.ARDUINO.write(bytes("stop;!",'utf-8'))
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

            self.get_logger().info("Movement msg to serial: stop;!")
            self.connecting = False
        except:
            self.get_logger().warn(
                f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s"
            )
            self.connecting = True
            self.connect_serial

    '''
    Shuts down node, serves as a callback for interrupt signal
    '''
    def graceful_shutdown(self, sig, frame) -> None:
        self.get_logger().info("Terminating all threads...")
        self.run = False
        self.tp_executor.shutdown()
        self.get_logger().info("Shutting node down...")
        rclpy.shutdown()
        raise SystemExit

    """
    Reader thread loop running read_serial as long as self.run
    Publishes the ArmState to the /arm_feedback topic
    """
    def read_loop(self):
        time.sleep(1)
        self.get_logger().info("Reading from serial...")
        
        while self.run:

            #self.get_logger().info(str(self.connecting))
            #self.get_logger().info(str(self.ARDUINO.in_waiting))
            if not self.connecting and self.ARDUINO.in_waiting:
                
                byte_chunk = self.ARDUINO.read_until(b'!')
                
                self.tp_executor.submit(self.publishMessage, byte_chunk[:-1])
                self.get_logger().info(byte_chunk)

        # sends kill signal to the read process
        os.kill(os.getpid(), 9)

    """
    Executes derived movement from the Joy (usually "/joy") topic
    """
    def write_serial(self):
        if not self.connecting and not self.zeroing:
            try:
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
                self.ARDUINO.write(bytes(self.movement,'utf-8'))
                self.get_logger().info(f"Movement msg to serial: {self.movement}")
                signal.setitimer(signal.ITIMER_REAL, 0, 0)

                #self.check_threads()

            except:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
                self.get_logger().warn("Connection Error: could not write serial")
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

                #self.check_threads()

        else:
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

    def check_threads(self):
        if (self.reader.done()):
            self.get_logger().info("Reader thread is dead, restarting...")
            self.reader = self.tp_executor.submit(self.read_loop)
        
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
        
        if "f" in string_message and not self.zeroing:
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

        elif (string_message == "zeroingDone;!"):
            self.zeroing = False
            self.get_logger().info("Zeroing done")
        
                
    # Action Server Callbacks
    '''
    Callback for when a zeroing goal is recieved
    '''
    def zero_execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')

        joint = goal_handle.request.joint

        self.movement = f"zero{joint};!"
        self.write_serial()
        
        self.zeroing = True
        
        result = ZeroArm.Result()
        
        while self.zeroing:
            if goal_handle.is_cancel_requested:
                self.zeroing = False
                self.get_logger().info('Canceling goal...')
                self.force_stop()
                goal_handle.canceled()
                return result

        result.result = True
        goal_handle.succeed()

        return result
        
    '''
    Callback for when a cancel request is recieved
    '''    
    def zero_cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT
        
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
    router_node = Router() # class above
    
    '''
    rclpy.spin(router_node) # spin = debounce (run for as long as it's on)
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise
    '''

    executor = MultiThreadedExecutor()  # for multiple threads

    rclpy.spin(router_node, executor = executor) # spin = debounce (run for as long as it's on)
    rclpy.shutdown() # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise
    


if __name__ == "__main__":
    main()