import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from keyboard_msgs.msg import Key
import serial
import threading

# Open serial port
port = serial.Serial(port='/dev/ttyUSB0', baudrate=115200, timeout=0.01)

class SensorArrayInterface(Node):
    def __init__(self):
        super().__init__("sensor_array_interface")
        
        # ROS2 interfaces
        self.soilCollectionSub = self.create_subscription(Key, "keydown", self.soilCollectionCB, 10)
        self.publisher_ = self.create_publisher(String, 'sensorData', 10)

        # Start a background thread for reading serial data
        self.serial_thread = threading.Thread(target=self.read_serial_loop, daemon=True)
        self.serial_thread.start()

    def soilCollectionCB(self, msg):
        msg_code = int(msg.code)
        port.write(bytes(str(msg_code) + "f", 'utf-8'))
        self.get_logger().info("start!")

    def read_serial_loop(self):
        """ Continuously read from serial and publish data immediately. """
        while rclpy.ok():
            if port.in_waiting > 0:
                raw_line = port.readline().decode('utf-8').strip()
                if raw_line:  # Only publish non-empty lines
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
