#!/usr/bin/python3

from typing import NamedTuple, TypeVar

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from enum import Enum
from std_msgs.msg import String
from pynput import keyboard
import numpy as np
from std_msgs.msg import Float32

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

"""
Node that interfaces between spacemouse joy node (receive spacemouse arrays) 
and the servo node (sends TwistStamped msgs)
"""
class IK_Controller(Node):

    class Motor(Enum):
        TW = 0
        L1 = 1
        L2 = 2
        WP = 3
        WR = 4
        EE = 5

    def __init__(self, node_name: str = "controller"):
        super().__init__(node_name)

        # Pubs and subs
        self.keyb_vel_sub = self.create_subscription(Float32, "/joy_vel", self.keyb_cb, 20)
        self.joy_sub = self.create_subscription(Joy, "/arm_ik_joy", self.joy_cb, 20)
        self.servo_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 20)

        # Info
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")


        # Create an instance of TwistStamped
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.header.frame_id = 'base_footprint'


        self.STOP = [0.0,0.0,0.0,0.0,0.0,0.0] # default of what stop is
        self.prev = [] #prev array of joy values (float array)
        self.curr = []

        # Parameters obtained from launch file, otherwise default
        self.pub_rate = self.get_param("pub_rate", rclpy.Parameter.Type.DOUBLE, 20.0) #Hz
        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.35) #spacemouse deadband

        # Local parameters
        self.max_vel = 1.0 #controls vels for all joints, can in/decrease with keyboard

        # All about the publishing loop
        self.run = True  # threads will stop running if false
        self.tp_executor = ThreadPoolExecutor(max_workers=1)
        self.pub_loop = self.tp_executor.submit(self.publishLoop)

    # Callback this time around just changes self.twist_stamped_msg
    # so that self.pub_loop can publish at a constant self.pub_rate
    def joy_cb(self, message: Joy) -> None:

        # print message
        #self.get_logger().info(str(message.axes))
        #self.get_logger().info(str(message.buttons))

        self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()

        self.curr = [message.axes[1],message.axes[0],message.axes[3],message.axes[4],message.axes[5],message.axes[2]]
        self.arrayNearestInt()

        if self.curr != self.prev:

            self.prev = self.curr

            if self.floatArrayEqual(self.curr, self.STOP):

                # twist already 0
                # handle roll and ee
                self.get_logger().info("handle roll ee")

            else: # send cmds

                # Map linear and angular vels with controller
                # Linear velocity in x-direction
                self.twist_stamped_msg.twist.linear.x = self.curr[0]  #left right main joy
                self.twist_stamped_msg.twist.linear.y = self.curr[1]  #forward backward main joy
                self.twist_stamped_msg.twist.linear.z = self.curr[2]  #speed axis

                # Angular velocity around x-axis
                self.twist_stamped_msg.twist.angular.x = self.curr[3] #left right small joy
                self.twist_stamped_msg.twist.angular.y = self.curr[4] #forward backward small joy
                self.twist_stamped_msg.twist.angular.z = self.curr[5] #twist main joy


                # Print array
                self.get_logger().info("\n")
                for m in self.Motor:
                    self.get_logger().info(str(m) + ": " + str(self.curr[m.value]))


    """
    Gets a velocity from the publisher on the keyboard node
    Updates what the max velocity will be when publishing delta twist cmds
    """
    def keyb_cb(self, message: Float32) -> None:
        self.max_vel = round(message.data, 1)

    """
    Makes sure messages are always being published and at a specific rate
    """
    def publishLoop(self):
        while self.run:
            self.servo_pub.publish(self.twist_stamped_msg)
            sleep(1.0/self.pub_rate)

    """
    Snaps values into the nearest min/max value depending on the deadband
    ex: 0.11166 -> 0.0 since < 0.35 deadband
        0.5 -> 1.0 since > 0.35 deadband and max is 1.0
    """
    def arrayNearestInt(self):

        for i in range(len(self.curr)):
            if (self.curr[i] > self.deadband):
                self.curr[i] = self.max_vel
            elif (self.curr[i] < -self.deadband):
                self.curr[i] = -self.max_vel
            else:
                self.curr[i] = 0.0

    
    def floatArrayEqual(self, arr1, arr2, tol=1e-5):
        arr1 = np.array(arr1)
        arr2 = np.array(arr2)
        return np.all(np.abs(arr1 - arr2) < tol * np.maximum(np.abs(arr1), np.abs(arr2)))

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

        # Must declare existence of parameter before retrieving it
        self.declare_parameter(param_name, param_type)

        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = Parameter(param_name, param_type, default_val)
            # Returns parameter if it exists, else returns default_param
            param_val = self.get_parameter_or(param_name, default_param).value

        assert param_val is not None, "The parameter received was None."

        if logging:
            self.get_logger().info(f"Using {param_name}: {param_val}")

        return param_val

"""
Most of the code below should remain unchanged except maybe the node names
""" 
def main(args=None):
    rclpy.init(args=args)           # if any args specified on node startup (via ros2 run <package> <node> args...)
    ikcontroller = IK_Controller()   # class above
    rclpy.spin(ikcontroller)        # spin = debounce (run for as long as it's on)
    IK_Controller.run = False      # to stop running pub loop, so thread can die gracefully
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
