import rclpy
from rclpy.node import Node
from keyboard_msgs.msg import Key
import time

import serial

port = serial.Serial(port = '/dev/ttyACM0', baudrate= 15200, timeout=0.25)

class MCU_interface_node(Node):
    def __init__(self):
        super().__init__("MCU_interface_node")
        self.soilCollectionSub = self.create_subscription(Key, "keydown", self.soilCollectionCB, 10)
        self.soilCollectionSub = self.create_subscription(Key, "keyup", self.soilCollectionCB, 10)
 
    def soilCollectionCB(self, msg):
        msg = msg.code
        if msg == 102:
            print("hello")
            port.write(bytearray('f','ascii'))
        elif msg == 274:
            port.write(bytearray('d','ascii'))
        elif msg == 273:
            port.write(bytearray('u','ascii'))
        elif msg == 119:
            port.write(bytearray('w','ascii'))
        elif msg == 115:
            port.write(bytearray('s','ascii'))
        elif msg == 120:
            port.write(bytearray('x','ascii'))
        elif msg == 122:
            port.write(bytearray('z','ascii'))
        elif msg == 49:
            port.write(bytearray('a','ascii'))
        elif msg == 50:
            port.write(bytearray('b','ascii'))
        elif msg == 51:
            port.write(bytearray('c','ascii'))
        elif msg == 52:
            port.write(bytearray('e','ascii'))
        elif msg == 53:
            port.write(bytearray('g','ascii'))
        elif msg == 54:
            port.write(bytearray('r','ascii'))
        elif msg == 118:
            port.write(bytearray('v','ascii'))
        elif msg == 112:
            port.write(bytearray('p','ascii'))
        elif msg == 121:
            port.write(bytearray('y','ascii'))
        # msg = int(msg.code)
        # print(bytes( str(msg) + "f", 'utf-8'))
        # port.write(bytes( str(msg) + "f", 'utf-8'))
        # self.get_logger().info(port.readline())
        


def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MCU_interface_node())
    MCU_interface_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()