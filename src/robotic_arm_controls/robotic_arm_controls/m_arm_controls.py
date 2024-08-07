#!/usr/bin/python3

import rclpy
from rclpy.node import Node
from general_interfaces.msg import ToggleMessage
from typing import TypeVar


T = TypeVar("T")

class MArmControllerNode(Node):

    def __init__(self, node_name: str = "m_arm_controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        #Subscribers
        self.subscriber = self.create_subscription(ToggleMessage, "/m_joy", self.toggle_callback, 20)

        #Publishers
        self.router_publisher = self.create_publisher(ToggleMessage, '/manual_states', 20)

    def toggle_callback(self, message: ToggleMessage):
        newMessage = ToggleMessage()

        self.get_logger().info(f"Publilshing to /manual_states:")

        newMessage.tw = -int(round(512*message.tw*message.speed, 0))
        newMessage.la1 = int(round(300*message.la1*message.speed,0))
        newMessage.la2 = int(round(300*message.la2*message.speed,0))
        newMessage.wr_roll = int(round(512*message.wr_roll*message.speed,0))
        newMessage.wr_pitch = int(round(512*message.wr_pitch*message.speed,0))
        newMessage.ee = int(round(512*message.ee*message.speed,0))

        self.router_publisher.publish(newMessage)
        self.get_logger().info(f"Published message: {newMessage.tw}, {newMessage.la1}, {newMessage.la2}, {newMessage.wr_pitch}, {newMessage.wr_roll}, {newMessage.ee}")

def main(args=None):
    rclpy.init(args=args)
    m_arm_controller_node = MArmControllerNode()
    rclpy.spin(m_arm_controller_node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()