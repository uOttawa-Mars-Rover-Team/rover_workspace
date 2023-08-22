import struct

import rclpy
import serial
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.parameter import Parameter


class SimpleDriveNode(Node):
    def __init__(self, node_name: str = "simple_drive"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")
        self.subscription = self.create_subscription(
            Twist, "cmd_vel", self.send_data_callback, 10
        )

        # Get parameters for the serial connection
        self.declare_parameter("serial_device", rclpy.Parameter.Type.STRING)
        serial_device = (
            self.get_parameter("serial_device").get_parameter_value().string_value
        )
        self.get_logger().info(f"Using serial device: {serial_device}")
        self.declare_parameter("baudrate", rclpy.Parameter.Type.INTEGER)
        baudrate = (
            self.get_parameter_or(
                "baudrate", Parameter("baud", rclpy.Parameter.Type.INTEGER, 9600)
            )
            .get_parameter_value()
            .integer_value
        )
        self.get_logger().info(f"Using baud rate: {baudrate}")

        # Setup the serial connection and specify the port after initialization
        # to prevent the connection from being opened immediately
        self.serial = serial.Serial(baudrate=baudrate)
        self.serial.port = serial_device

    def send_data_callback(self, message: Twist) -> None:
        self.serial.open()

        # Send a struct with little-endian byte order ("<") containing two
        # float values ("ff"), the linear x and angular z
        message_struct = struct.pack("<ff", message.linear.x, message.angular.z)
        serial_msg = b"\x00" + message_struct
        self.serial.write(serial_msg)

        self.serial.close()


def main(args=None):
    rclpy.init(args=args)
    simple_drive_node = SimpleDriveNode()
    rclpy.spin(simple_drive_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
