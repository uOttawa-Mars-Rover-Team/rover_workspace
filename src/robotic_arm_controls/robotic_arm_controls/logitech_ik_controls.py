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

        # Pubs and subs
        self.subscriber = self.create_subscription(Joy, "/arm_ik_joy", self.callback_function, 20)
        self.publisher = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 20)

        # Info
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")
        self.get_logger().info(f"Subscribing to messages from: {self.subscriber.topic_name}")
        self.get_logger().info(f"Publishing messages to: {self.publisher.topic_name}")


        # Create an instance of TwistStamped
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.header.frame_id = 'base_footprint'

        self.prev = [] #prev array of joy values (float array)
        self.curr = []

        # Params
        self.pub_rate = 10.0 #Hz
        self.deadband = 0.4

        # All about the publishing loop
        self.run = True  # threads will stop running if false
        self.tp_executor = ThreadPoolExecutor(max_workers=1)
        self.pub_loop = self.tp_executor.submit(self.publishLoop)


    # Callback this time around just changes self.twist_stamped_msg
    # so that self.pub_loop can publish at a constant self.pub_rate
    def callback_function(self, message: Joy) -> None:

        # print message
        #self.get_logger().info(str(message.axes))
        #self.get_logger().info(str(message.buttons))

        self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()

        self.curr = [message.axes[1],message.axes[0],message.axes[3],message.axes[4],message.axes[5],message.axes[2]]
        self.arrayNearestInt()

        if (self.curr != self.prev):

            self.prev = self.curr

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
            self.get_logger().info(' '.join(str(x) for x in self.curr))

    def publishLoop(self):
        while self.run:
            self.publisher.publish(self.twist_stamped_msg)
            sleep(1.0/self.pub_rate)

    def arrayNearestInt(self):

        for i in range(len(self.curr)):
            if (self.curr[i] > self.deadband):
                self.curr[i] = 1.0
            elif (self.curr[i] < -self.deadband):
                self.curr[i] = -1.0
            else:
                self.curr[i] = 0.0


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
    spacemousenode.run = False      # to stop running pub loop, so thread can die gracefully
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
