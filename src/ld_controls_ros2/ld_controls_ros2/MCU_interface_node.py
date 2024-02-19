import rclpy
from rclpy.node import Node

from std_msgs.msg import u_int8

class MCU_interface_node(node):
    def __init__(self):
        super().__init__("MCU_interface_node")
        self.publisher_ = self.create_publisher()

