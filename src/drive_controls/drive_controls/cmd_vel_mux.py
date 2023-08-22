import time

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.parameter import Parameter


class CmdVelMuxNode(Node):
    def __init__(self, node_name: str = "cmd_vel_mux"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")
        self.drive_control_publisher = self.create_publisher(Twist, "cmd_vel", 10)
        self.get_logger().info(
            f"Publishing messages at: {self.drive_control_publisher.topic}"
        )
        # Subscribe to human control messages
        self.human_control_subscription = self.create_subscription(
            Twist, "teleop/cmd_vel", self.human_control_callback, 10
        )
        self.get_logger().info(
            f"Subscribing to messages from: {self.human_control_subscription.topic}"
        )
        # Subscribe to autonomous control messages
        self.autonomous_control_subscription = self.create_subscription(
            Twist, "move_base/cmd_vel", self.autonomous_control_callback, 10
        )
        self.get_logger().info(
            f"Subscribing to messages from: {self.autonomous_control_subscription.topic}"
        )

        self.declare_parameter("block_duration", rclpy.Parameter.Type.INTEGER)
        self.default_autonomous_block_duration = (
            self.get_parameter_or(
                "block_duration",
                Parameter("block_duration", rclpy.Parameter.Type.INTEGER, 5),
            )
            .get_parameter_value()
            .integer_value
        )
        self.get_logger().info(
            f"Using block duration: {self.default_autonomous_block_duration}"
        )
        self.current_autonomous_block_duration = self.default_autonomous_block_duration
        self.last_human_control_time = time.time()

    def autonomous_control_callback(self, message: Twist) -> None:
        # Check to see if it's been enough time since the last human control
        # command was sent
        time_since_human_control = time.time() - self.last_human_control_time
        if time_since_human_control >= self.block_duration:
            # Stop blocking autonomous control
            self.block_duration = 0
            self.drive_control_publisher.publish(message)

    def human_control_callback(self, message: Twist) -> None:
        self.last_human_control_time = time.time()
        # Reset the block duration to prevent autonomous control commands from
        # taking over
        self.block_duration = self.default_autonomous_block_duration
        self.drive_control_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)
    cmd_vel_mux_node = CmdVelMuxNode()
    rclpy.spin(cmd_vel_mux_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
