#!/usr/bin/python3


from typing import NamedTuple, TypeVar

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

"""
Node that interfaces between spacemouse joy node (receive spacemouse arrays) 
and the servo node (sends TwistStamped msgs)
"""
class SpacemouseNode(Node):

    def __init__(self, node_name: str = "controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        self.subscriber = self.create_subscription(Joy, "/arm_ik_joy", self.callback_function, 20)

        self.publisher = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 20)

        self.get_logger().info(f"Subscribing to messages from: {self.subscriber.topic_name}")
        self.get_logger().info(f"Publishing messages to: {self.publisher.topic_name}")

    def callback_function(self, message: Joy) -> None:

        # print message
        #self.get_logger().info(str(message.axes))
        #self.get_logger().info(str(message.buttons))

        # Create an instance of TwistStamped
        twist_stamped_msg = TwistStamped()

        twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()

        # Set linear and angular velocities
        twist_stamped_msg.twist.linear.x = message.axes[1]  # Linear velocity in x-direction
        twist_stamped_msg.twist.linear.y = message.axes[0] 
        twist_stamped_msg.twist.linear.z = message.axes[2]  
        twist_stamped_msg.twist.angular.x = message.axes[4]  # Angular velocity around x-axis
        twist_stamped_msg.twist.angular.y = message.axes[3]  
        twist_stamped_msg.twist.angular.z = message.axes[5]

        self.publisher.publish(twist_stamped_msg)

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
    spacemousenode = SpacemouseNode()   # class above
    rclpy.spin(spacemousenode)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
