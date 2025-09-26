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
from general_interfaces.msg import GripperControl
from general_interfaces.msg import ToggleMessage

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

"""
Node that interfaces between spacemouse joy node (receive spacemouse arrays) 
and the servo node (sends TwistStamped msgs)
"""
class Joy_IK_Controller(Node):

    class Velocity(Enum):
        x = 0
        y = 1
        z = 2
        lx = 3
        ly = 4
        lz = 5

    def __init__(self, node_name: str = "joy_ik_controls"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Parameters obtained from launch file, otherwise default
        self.pub_rate = self.get_param("pub_rate", rclpy.Parameter.Type.DOUBLE, 20.0) # pub rate in Hz
        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.40) # spacemouse deadband
        self.mode = self.get_param("mode", rclpy.Parameter.Type.STRING, "I") # ik or manual mode, default I for ik
        self.dirWP = self.get_param("dirWP", rclpy.Parameter.Type.INTEGER, 1)
        self.dirWR = self.get_param("dirWR", rclpy.Parameter.Type.INTEGER, 1)
        self.dirTW = self.get_param("dirTW", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL1 = self.get_param("dirL1", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL2 = self.get_param("dirL2", rclpy.Parameter.Type.INTEGER, 1)


        
        # All about the publishing loop
        self.run = True  # threads will stop running if false
        self.tp_executor = ThreadPoolExecutor(max_workers=3)

        # Pubs, subs and their variables
        self.keyb_vel_sub = self.create_subscription(Float32, "/keyboard/arm_vel", self.keyb_cb, 20)
        self.keyb_vel_sub = self.create_subscription(Float32, "/keyboard/arm_vel_tw", self.keyb_tw_cb, 20)

        self.max_vel = 1.0 # set to max speed by default 
        self.max_vel_tw = 1.0

        self.servo_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 20)
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.header.frame_id = 'base_footprint'

        self.vel_control_pub = self.create_publisher(GripperControl, '/gripper_control/gripper_velocities', 20)
        self.vel_control_msg = GripperControl()
        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 20)

        self.joy_sub_logitech = self.create_subscription(Joy, "/joy/arm_cmd_logitech", self.joy_cb_logitech, 20)
        self.joy_sub_spacemouse = self.create_subscription(Joy, "/joy/arm_cmd_spacemouse", self.joy_cb_spacemouse, 20)


        self.command = String()
        self.curr_cmd = ""
        self.prev_cmd = "!"


        # Joystick/Spacemouse-related below
        self.STOP_AXES = [0.0,0.0,0.0,0.0,0.0,0.0] # default of what stop is for axes
        self.prev_axes = [0.0,0.0,0.0,0.0,0.0,-2.0] # previous array of joy axes values (float array)
        self.curr_axes = [0.0,0.0,0.0,0.0,0.0,0.0] # current  array of joy axes values

        self.STOP_BTNS    = [0,0,0,0,0,0] # default of what stop is for buttons
        self.prev_btns_lt = [0,0,0,0,0,0,0,0,0,0,0,0,0] # previous array of joy btn values for logitech controller (int array)
        self.curr_btns_lt = [0,0,0,0,0,0,0,0,0,0,0,0,0] # current  array of joy btn values
        self.prev_btns_sm = [0,0,0,0,0,0] # previous array of joy btn values; spacemouse(int array)
        self.curr_btns_sm = [0,0,0,0,0,0] # current  array of joy btn values
        
        # Permutations for the mapping for the spacemouse (sm)
        self.sm_btns = [0, 1]
        self.sm_axes = []
        if self.mode == "I":
            # mappings
            # 0 - fwd/bwd
            # 1 - sideways
            # 2 - twist around x
            # 3 - twist around y
            # 4 - twist around z
            # 5 - up down z
            self.sm_axes = [1, 0, 2, 5, 3, 4]
        else:
            self.sm_axes = [5, 1, 2, 3, 4, 0]

        self.lt_btns = [0,1,2,3,4,5,6,7,8,9,10,11]
        self.lt_axes = [2, 0, 1, 5, 4, 3]
        # logitech btns not needed since it's not used at all 

    # Callback this time around just changes self.twist_stamped_msg
    # so that self.pub_loop can publish at a constant self.pub_rate



    def joy_cb_logitech(self, message: Joy) -> None:
        btn_sum = 0
        btns_zero = True


        if (len(message.buttons) == 12): # more than 2 btns -> must be logitech controller
            # for i in range(6)
            #     self.curr_axes[i] = message.axes[self.lt_axes[i]]
            for i in range(12):
                btn_sum += message.buttons[i]
                self.curr_btns_lt[i] = message.buttons[self.lt_btns[i]]
            if btn_sum != 0:
                btns_zero = False

            self.curr_axes[2] = message.axes[self.lt_axes[3]]
            self.curr_axes[1] = message.axes[self.lt_axes[2]]
            self.curr_axes[0] = message.axes[self.lt_axes[0]]
            self.joy_parser(message)


            #self.get_logger().info("We got logitech")   
        elif (len(message.buttons) == 2):
            self.get_logger().info("Spacemouse wired to logitech port")
            
        else:
            self.get_logger().info("Wrong controller or spacemouse")   


    def joy_cb_spacemouse(self, message: Joy) -> None:
        if (len(message.buttons) == 2): # spacemouse
            # for i in range(6):
            #     self.curr_axes[i] = message.axes[self.sm_axes[i]]
            # for i in range(2):
            #     btn_sum += message.buttons[i]
            #     self.curr_btns_sm[i] = message.buttons[self.sm_btns[i]]
            # if btn_sum != 0:
            #     btns_zero = False

            self.curr_axes[3] = message.axes[3]
            self.curr_axes[4] = message.axes[4]
            self.joy_parser(message)


            #self.get_logger().info("We got space mouse")
        elif (len(message.buttons) == 12):
            self.get_logger().info("Logitech wired to spacemouse port")

        else:
            self.get_logger().info("Wrong controller brotha")

    def joy_parser(self, message: Joy) -> None:


    
        if not self.floatArrayEqual(self.curr_axes, self.prev_axes) or not btns_zero:
            self.prev_axes = self.curr_axes

            # Stop the whole arm if all axes & btn values are zero
            if not self.floatArrayEqual(self.curr_axes, self.STOP_AXES) or not btns_zero:

                # Rounds floats in self.curr_axes to either 0 or sign*max_vel (set by keyboard)
                self.arrayRoundToMaxVelocity()

                if self.mode == "I":

                    # Add current time to timestamp
                    self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()

                    # Map linear and angular vels with controller
                    # Linear velocity in x-direction
                    self.twist_stamped_msg.twist.linear.x = self.curr_axes[0]  #left right main joy
                    self.twist_stamped_msg.twist.linear.y = self.curr_axes[1]  #forward backward main joy
                    self.twist_stamped_msg.twist.linear.z = self.curr_axes[2]  #speed axis

                    # Angular velocity around x-axis
                    #self.twist_stamped_msg.twist.angular.x = self.curr_axes[3] #left right small joy
                    self.vel_control_msg.roll_velocity = self.curr_axes[3]
                    self.twist_stamped_msg.twist.angular.y = self.curr_axes[4] #forward backward small joy
                    self.twist_stamped_msg.twist.angular.z = self.curr_axes[5] #twist main joy

                    # Prepare vel cmd for ee stepper
                    if len(message.buttons) == 2: # spacemouse
                        if self.curr_btns_sm[0]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_sm[0] * self.max_vel
                        elif self.curr_btns_sm[1]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_sm[1] * self.max_vel

                    elif len(message.buttons) == 12: # logitech
                        if self.curr_btns_lt[0]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_lt[0] * self.max_vel
                        elif self.curr_btns_lt[1]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_lt[1] * self.max_vel

                    # Print array
                    #self.get_logger().info("\n")
                    #for v in self.Velocity:
                    #    self.get_logger().info(str(v) + ": " + str(self.curr_axes[v.value]))
                    #    self.get_logger().info("Roll: " + str(self.vel_control_msg.roll))
                    #    self.get_logger().info("EE: " + str(self.vel_control_msg.ee))


                    self.tp_executor.submit(self.servo_pub_cmd, self.twist_stamped_msg)
                    self.tp_executor.submit(self.vel_control_cmd, self.vel_control_msg)

                else:
                    self.curr_cmd = "S;"

                    self.curr_cmd += str(round(self.curr_axes[0]*self.dirTW, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[1]*self.dirL1, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[2]*self.dirL2, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[3]*self.dirWP, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[4]*self.dirWR, 2))
                    self.curr_cmd += ";"

                    # if len(message.buttons) == 2: # spacemouse
                        
                    #     if self.curr_btns_sm[0]:
                    #         self.curr_cmd += str(round(self.max_vel, 2))
                    #     elif self.curr_btns_sm[1]:
                    #         self.curr_cmd += str(-round(self.max_vel, 2))
                    #     else:
                    #         self.curr_cmd += "0.0"
                            
                    # elif len(message.buttons) == 12: # logitech
                    if self.curr_btns_lt[0]:
                        self.curr_cmd += str(round(self.max_vel, 2))
                    elif self.curr_btns_lt[1]:
                        self.curr_cmd += str(-round(self.max_vel, 2))
                    else:
                        self.curr_cmd += "0.0"
                    self.curr_cmd += ";!"

                    if self.curr_cmd != self.prev_cmd:
                        self.prev_cmd = self.curr_cmd
                        self.command.data = self.curr_cmd
                        self.tp_executor.submit(self.cmd_pub_cmd, self.command)

    """
    Makes sure messages are always being published and at a specific rate
    """
    def servo_pub_cmd(self, servo_msg):
        self.servo_pub.publish(servo_msg)

    """
    Makes sure messages are always being published and at a specific rate
    """
    def vel_control_cmd(self, vel_msg):
        self.vel_control_pub.publish(vel_msg)

    """
    Makes sure messages are always being published and at a specific rate
    """
    def cmd_pub_cmd(self, cmd_msg):
        self.get_logger().info("Command sent: " + cmd_msg.data)
        self.cmd_pub.publish(cmd_msg)

    """
    Snaps values into the nearest min/max value depen4ing on the deadband
    ex: 0.11166 -> 0.0 since < 0.35 deadband
        0.5 -> 1.0 since > 0.35 deadband and max is 1.0
    """
    def arrayRoundToMaxVelocity(self):

        for i in range(1, len(self.curr_axes)):
            if (self.curr_axes[i] > self.deadband):
                self.curr_axes[i] = self.max_vel
            elif (self.curr_axes[i] < -self.deadband):
                self.curr_axes[i] = -self.max_vel
            else:
                self.curr_axes[i] = 0.0

        if (self.curr_axes[0] > self.deadband):
            self.curr_axes[0] = self.max_vel_tw
        elif (self.curr_axes[0] < -self.deadband):
            self.curr_axes[0] = -self.max_vel_tw
        else:
            self.curr_axes[0] = 0.0
    

    """
    Gets a velocity from the publisher on the keyboard node
    Updates what the max velocity will be when publishing delta twist cmds
    """
    def keyb_cb(self, message: Float32) -> None:
        self.max_vel = round(message.data, 1)

    def keyb_tw_cb(self, message: Float32) -> None:
        self.max_vel_tw = round(message.data, 1)    

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
    controller = Joy_IK_Controller()   # class above
    rclpy.spin(controller)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
