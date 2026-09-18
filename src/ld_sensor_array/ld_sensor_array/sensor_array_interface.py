import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import threading

class SensorArrayInterface(Node):
    def __init__(self):
        super().__init__("sensor_array_interface")

        # Declare and get parameter
        self.declare_parameter("serial_port", "/dev/ttyUSB0")
        port_path = self.get_parameter("serial_port").get_parameter_value().string_value

        # Open serial port
        self.port = serial.Serial(port=port_path, baudrate=115200, timeout=0.01)

        # ROS2 publisher
        self.publisher_ = self.create_publisher(String, 'sensorData', 10)

        # Start a background thread for reading serial data
        self.serial_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.serial_thread.start()

    def read_serial_loop(self):
        while rclpy.ok():
            if self.port.in_waiting > 0:
                raw_line = self.port.readline().decode('utf-8').strip()
                if raw_line:
                    self.get_logger().info(raw_line)
                    msg = String()
                    msg.data = raw_line
                    self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = SensorArrayInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
