"""Translate arm teleop strings to ros2_control velocity commands."""

import math
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String

from robotic_arm_controls.sim_command import velocity_command


class SimCommandBridge(Node):
    """Bridge six channels in TW, EL, SL, WP, WR, EE order."""

    def __init__(self):
        super().__init__("sim_command_bridge")
        self.declare_parameter("velocity_scales", [0.25] * 6)
        self.declare_parameter("output_indices", [0, 1, 2, 3, 4, 5])
        self.indices = list(self.get_parameter("output_indices").value)
        if (
            not self.indices
            or any(type(i) is not int or i < 0 or i > 5 for i in self.indices)
            or len(set(self.indices)) != len(self.indices)
        ):
            raise ValueError("output_indices must contain unique indices from 0 to 5")
        self.get_logger().warning(
            f"Simulation output channel indices: {self.indices}. "
            "Omitted channels are not simulated."
        )
        self.declare_parameter("command_timeout", 0.3)
        self.declare_parameter("output_topic", "/arm_velocity_controller/commands")
        self.scales = list(self.get_parameter("velocity_scales").value)
        velocity_command("stop;!", self.scales)
        self.timeout = self.get_parameter("command_timeout").value
        if not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("command_timeout must be positive and finite")
        self.publisher = self.create_publisher(
            Float64MultiArray, self.get_parameter("output_topic").value, 10
        )
        self.values = [0.0] * 6
        self.last_command = float("-inf")
        self.create_subscription(String, "/arm_cmd", self.on_command, 10)
        self.create_timer(0.02, self.publish_command)
        self.get_logger().warning(
            "SIMULATION ONLY: scales are provisional; joint order must match "
            "input channel order: TW, L1/EL, L2/SL, WP, WR, EE."
        )

    def on_command(self, message):
        try:
            self.values = velocity_command(message.data, self.scales)
            self.last_command = time.monotonic()
        except ValueError as error:
            self.values = [0.0] * 6
            self.last_command = float("-inf")
            self.get_logger().warning(f"Stopped simulation command: {error}")
        self.publish_command()

    def publish_command(self):
        values = self.values if time.monotonic() - self.last_command < self.timeout else [0.0] * 6
        self.publisher.publish(Float64MultiArray(data=[values[i] for i in self.indices]))


def main(args=None):
    rclpy.init(args=args)
    node = SimCommandBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.publisher.publish(Float64MultiArray(data=[0.0] * len(node.indices)))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
