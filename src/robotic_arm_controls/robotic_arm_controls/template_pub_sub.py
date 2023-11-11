#!/usr/bin/python3

import time
from typing import NamedTuple, TypeVar

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy
from std_msgs.msg import String

T = TypeVar("T")

class TemplateNode(Node):
    """
    Initializes a node used to receive messages from the "input_topic" and send
    messages associated with these control commands to the topic "output_topic"
    """

    def __init__(self, node_name: str = "controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Joy subscriber
        # Runs the callback_function every time a msg is received
        self.subscriber = self.create_subscription(
            String, "input_topic", self.callback_function, 20
        )

        self.publisher = self.create_publisher(
            String, 'output_topic', 20
        )

        self.get_logger().info(
            f"Subscribing to messages from: {self.subscriber.topic_name}"
        )

    """
    Main loop for processing input
    """
    def callback_function(self, message: String) -> None:

        # all we do here is print the received message
        print(*message.data)
        self.get_logger().info(str(*message.data))

        # and then publish it
        self.publisher.publish(str(*message.data))

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
    rclpy.init(args=args)
    templatenode = TemplateNode()
    rclpy.spin(templatenode)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
