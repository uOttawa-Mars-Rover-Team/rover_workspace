#!/usr/bin/env python

import random

import rclpy
from rclpy.node import Node

from general_interfaces.msg import MotorData, PowerData


class MyPublisher(Node):
    def __init__(self, node_name: str = "ex_publisher"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Create a PD publisher
        self.pd_publisher = self.create_publisher(PowerData, "PowerData", 10)
        self.get_logger().info(
            f"Publishing PD messages at: {self.pd_publisher.topic_name}"
        )

        # Create a MD publisher
        self.md_publisher = self.create_publisher(MotorData, "MotorData", 10)
        self.get_logger().info(
            f"Publishing MD messages at: {self.md_publisher.topic_name}"
        )

        # Set a timer to call publish_data() every 2 seconds (0.5Hz).
        timer_period = 2
        self.get_logger().info(f"Publishing data every {timer_period} seconds")
        self.timer = self.create_timer(timer_period, self.publish_data)

    def publish_data(self):
        # PowerData publishing
        currents = [round(random.random() * 4, 2) for i in range(16)]
        message = PowerData(
            voltage=12.0 + random.uniform(-1, 1), currents=currents, filled=4
        )

        self.pd_publisher.publish(message)
        self.get_logger().info(f"Published a PD message: {message}")

        # MotorData publishing
        message = MotorData(
            velocity_feedback=random.uniform(2, 5),
            positon_feedback=random.uniform(-100, 100),
            output_current=random.uniform(4, 6),
            output_voltage=12 + random.uniform(-1, 1),
            sticky_faults=random.choice(["Right Side", "Left Side"]),
            faults_bitfield=random.randrange(6),
        )
        self.md_publisher.publish(message)
        self.get_logger().info(f"Published a MD message: {message}")


def main(args=None):
    rclpy.init(args=args)
    node = MyPublisher()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
