#!/usr/bin/python3                 

from typing import NamedTuple, TypeVar # For parameter helper function

import rclpy # rospy for ROS2
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import Joy
from std_msgs.msg import String

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

class AxesValues(NamedTuple):
    """
    Define properties for each of the 6 axes on the joystick. Use default
    property names for unused vales.
    """

    axes_0: float 
    actuator: float 
    tower: float 
    speed_axis: float 
    wrist_roll: float
    wrist_pitch: float

class ButtonValues(NamedTuple):
    """
    Define properties for each of the 1.02 buttons on the joystick. Use default
    property names for unused vales.
    """

    ee_close_btn: int
    ee_open_btn: int
    second_speed_btn: int
    third_speed_btn: int
    lowest_speed_btn: int
    norm_speed_btn: int
    btn_6: int 
    mn_mode_switch: int 
    ik_mode_switch: int 
    btn_9: int 
    zeroing_btn: int 
    actuator_hold_btn: int 

class IkJoy(Node):
    MANUAL_MODE = "m"
    IK_MODE = "ik"
    
    def __init__(self, node_name: str = "ikjoy"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        #Subscribers
        self.subscriber = self.create_subscription(Joy, "/arm_joy", self.joy_callback, 20)

        #Publishers
        self.ik_publisher = self.create_publisher(TwistStamped, '/delta_twist_cmds', 20)

        # The node's logger, may just use print() instead
        self.get_logger().info(f"Subscribing to messages from: {self.subscriber.topic_name}")
            
    '''
    Callback for the joystick subscriber. This method is called whenever a message is received from the joystick
    '''
    def joy_callback(self, message: Joy):
        axes_values = AxesValues(*message.axes)
        btn_values = ButtonValues(*message.buttons)
        
        newTwistStamped =  TwistStamped()

        if axes_values.axes_0 > 0:
            newTwistStamped.twist.linear.y = 1.0
        elif axes_values.axes_0 < 0:
            newTwistStamped.twist.linear.y = -1.0
        else:
            newTwistStamped.twist.linear.y = 0.0
        
        if axes_values.actuator > 0:
            newTwistStamped.twist.linear.z = 1.0
        elif axes_values.actuator < 0:
            newTwistStamped.twist.linear.z = -1.0
        else:
            newTwistStamped.twist.linear.z = 0.0

        if axes_values.tower > 0:
            newTwistStamped.twist.linear.x = 1.0
        elif axes_values.tower < 0:
            newTwistStamped.twist.linear.x = -1.0
        else:
            newTwistStamped.twist.linear.x = 0.0

        if axes_values.wrist_roll > 0:
            newTwistStamped.twist.angular.z = 1.0
        elif axes_values.wrist_roll < 0:
            newTwistStamped.twist.angular.z = -1.0
        else:
            newTwistStamped.twist.angular.z = 0.0

        if axes_values.wrist_pitch > 0:
            newTwistStamped.twist.angular.y = 1.0
        elif axes_values.wrist_pitch < 0:
            newTwistStamped.twist.angular.y = -1.0
        else:
            newTwistStamped.twist.angular.y = 0.0

        if btn_values.ee_close_btn == 1.0:
            newTwistStamped.twist.angular.x = 1.0
        elif btn_values.ee_open_btn == 1.0:
            newTwistStamped.twist.angular.x = -1.0
        else:
            newTwistStamped.twist.angular.x = 0.0

        self.ik_publisher.publish(newTwistStamped)

def main(args=None):
    rclpy.init(args=args)           # if any args specified on node startup (via ros2 run <package> <node> args...)
    ik_joy_node = IkJoy()   # class above
    rclpy.spin(ik_joy_node)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise

if __name__ == "__main__":
    main()