import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from std_msgs.msg import String
from keyboard_msgs.msg import Key
import time

import serial

port = serial.Serial(port = '/dev/ttyACM0', baudrate= 9600)

class MCU_interface_node(Node):
    def __init__(self):
        super().__init__("MCU_interface_node")
        self.soilCollectionSub = self.create_subscription(Key, "keydown", self.soilCollectionCB, 10)
 
    def soilCollectionCB(self, msg):
        msg = msg.code
        if msg == 102:
            port.write()


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MCU_interface_node())
    MCU_interface_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()