#!/usr/bin/python3


from typing import NamedTuple, TypeVar # For parameter helper function

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String # msg used by publisher and subscriber

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

"""
Initializes a node used to receive messages from the "input_topic" and send
messages associated with these control commands to the topic "output_topic"
"""
class TemplateNode(Node):

    def __init__(self, node_name: str = "controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        """
        - String is the msg type
        - 'input_topic' is the topic for which to listen to
           (can test this by running: ros2 topic pub /input_topic std_msgs/msg/String "data: sadvfdshdsf")
        - self.callback_function is executed on every receipt of a msg
        - 20: queue size (msgs to keep in case node is slowed down)
        """
        self.subscriber = self.create_subscription(
            String, "input_topic", self.callback_function, 20
        )

        """
        Pretty much the same as above
        - output_topic: the topic to publish to
          (can listen by running: ros2 topic echo /output_topic)
        """
        self.publisher = self.create_publisher(
            String, 'output_topic', 20
        )

        # Note: you can have as many pub/sub as you want; don't push the limits tho

        # The node's logger, may just use print() instead
        self.get_logger().info(
            f"Subscribing to messages from: {self.subscriber.topic_name}"
        )

    """
    Main loop for processing input and/or outputting
    """
    def callback_function(self, message: String) -> None:

        # print message
        self.get_logger().info(str(message.data))

        # process, encode, do whatever here...

        # and then publish it
        self.publisher.publish(message)

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

"""
Most of the code below should remain unchanged except maybe the node names
"""
def main(args=None):
    rclpy.init(args=args)           # if any args specified on node startup (via ros2 run <package> <node> args...)
    templatenode = TemplateNode()   # class above
    rclpy.spin(templatenode)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()
