#!/usr/bin/python3

from typing import NamedTuple, TypeVar

import rclpy # rospy fomsg import String
from sensor_msgs.msg import Joy
from rclpy.parameter import Parameter
from rclpy.node import Node
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
class Joy_M_Controller(Node):

    def __init__(self, node_name: str = "joy_m_controls"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Parameters obtained from launch file, otherwise default
        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.40) # spacemouse deadband

        # Pubs, subs and their variables
        self.keyb_vel_sub = self.create_subscription(Float32, "/keyboard/arm_vel", self.keyb_cb, 20)
        self.max_vel = 0.5 # subscribing to the keyboard, changes according to a dial

        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 20)
        self.command = String()
        self.curr_cmd = ""
        self.prev_cmd = "!"

        self.axesZero = False
        self.btnsZero = False

        self.joy_sub = self.create_subscription(Joy, "/joy/arm_cmd", self.joy_cb, 20)
        
        # Permutations for the mapping for the spacemouse (sm)
        # mappings
        # 0 - fwd/bwd
        # 1 - sideways
        # 2 - twist around x
        # 3 - twist around y
        # 4 - twist around z
        # 5 - up down z
        self.mapping = [1, 0, 2, 5, 3, 4]

    # Callback this time around just changes self.twist_stamped_msg
    # so that self.pub_loop can publish at a constant self.pub_rate
    def joy_cb(self, message: Joy) -> None:

        # check if zero; ie stop
        for i in range(6):
            if abs(message.axes[i]) - self.deadband > 0:
                self.axesZero = False
                break
        for i in range(2):
            if message.buttons[i]:
                self.btnsZero = False
                break

        if (not self.axesZero or not self.btnsZero):

            self.command = String()
            self.curr_cmd = "S;"
            self.max_vel = round(self.max_vel, 1)

            if message.axes[5] > 0:
                self.curr_cmd += str(round(self.max_vel, 2))
            elif message.axes[5] < 0:
                self.curr_cmd += str(round(-self.max_vel, 2))
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";"
            if message.axes[1] > 0:
                self.curr_cmd += str(round(self.max_vel, 2))
            elif message.axes[1] < 0:
                self.curr_cmd += str(round(-self.max_vel, 2))
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";"
            if message.axes[2] > 0:
                self.curr_cmd += str(round(-self.max_vel, 2))
            elif message.axes[2] < 0:
                self.curr_cmd += str(round(self.max_vel, 2))
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";"
            if message.axes[3] > 0:
                self.curr_cmd += str(round(self.max_vel, 2))
            elif message.axes[3] < 0:
                self.curr_cmd += str(round(-self.max_vel, 2))
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";"
            if message.axes[4] > 0:
                self.curr_cmd += str(round(self.max_vel, 2))
            elif message.axes[4] < 0:
                self.curr_cmd += str(round(-self.max_vel, 2))
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";"
                
            if message.buttons[0]:
                self.curr_cmd += str(self.max_vel*0.5)
            elif message.buttons[1]:
                self.curr_cmd += str(-self.max_vel*0.5)
            else:
                self.curr_cmd += "0.0"
            self.curr_cmd += ";!"

            if self.curr_cmd != self.prev_cmd:
                self.prev_cmd = self.curr_cmd
                self.command.data = self.curr_cmd
                self.cmd_pub.publish(self.command)
                self.get_logger().info(self.command.data)

        else: #both axes and btns are at neutral position, so stop
        
            self.curr_cmd = "S;0;0;0;0;0;0;!"
            if self.curr_cmd != self.prev_cmd:
                self.prev_cmd = self.curr_cmd
                self.command.data = self.curr_cmd
                self.cmd_pub.publish(self.command)
                self.get_logger().info(self.command.data)

    """
    Gets a velocity from the publisher on the keyboard node
    Updates what the max velocity will be when publishing delta twist cmds
    """
    def keyb_cb(self, message: Float32) -> None:
        self.max_vel = round(message.data, 1)

    """
    Helper function to compare two float arrays
    """
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
    controller = Joy_M_Controller()   # class above
    rclpy.spin(controller)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
