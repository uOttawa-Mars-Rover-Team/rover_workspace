import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import sys


class GeigerPublisherNode(Node):
    """
    A ROS 2 node that reads data from a serial port (e.g., a Geiger counter)
    and publishes it to a specified topic.
    """

    def __init__(self):
        super().__init__("geiger_publisher_node")

        # Declare parameters with default values
        self.declare_parameter("port", "/dev/ttyTHS1")
        self.declare_parameter("baud_rate", 115200)
        self.declare_parameter("topic_name", "geiger/data")

        # Get parameter values
        self.port = self.get_parameter("port").get_parameter_value().string_value
        self.baud_rate = (
            self.get_parameter("baud_rate").get_parameter_value().integer_value
        )
        self.topic_name = (
            self.get_parameter("topic_name").get_parameter_value().string_value
        )

        self.get_logger().info(f"Using port: {self.port}, baud rate: {self.baud_rate}")
        self.get_logger().info(f"Publishing to topic: {self.topic_name}")

        # Create the publisher
        self.publisher_ = self.create_publisher(String, self.topic_name, 10)

        # Initialize serial connection
        self.ser = None
        try:
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1.0)
            self.get_logger().info(f"Successfully opened serial port: {self.port}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to open serial port {self.port}: {e}")
            # Exit or handle the error appropriately
            sys.exit(1)

        # Create a timer to call the read_and_publish method periodically.
        # The timeout on readline() will be the main rate limiter.
        # A 0.01s timer ensures we check for new data frequently.
        self.timer = self.create_timer(0.01, self.read_and_publish)

    def read_and_publish(self):
        """
        Reads a line from the serial port and publishes it if not empty.
        """
        if self.ser and self.ser.is_open:
            try:
                # readline() will block until a newline is received or the timeout is reached.
                line = self.ser.readline().decode("ascii").strip()
                if line:
                    msg = String()
                    msg.data = line
                    self.publisher_.publish(msg)
                    self.get_logger().info(f'Publishing: "{msg.data}"')
            except serial.SerialException as e:
                self.get_logger().error(f"Serial read error: {e}")
            except UnicodeDecodeError as e:
                self.get_logger().warn(f"Unicode decode error: {e}. Ignoring line.")

    def destroy_node(self):
        """
        Custom cleanup method to close the serial port on shutdown.
        """
        if self.ser and self.ser.is_open:
            self.get_logger().info("Closing serial port.")
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    geiger_node = GeigerPublisherNode()
    try:
        rclpy.spin(geiger_node)
    except KeyboardInterrupt:
        pass
    finally:
        # The destroy_node method will be called automatically on shutdown
        geiger_node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
