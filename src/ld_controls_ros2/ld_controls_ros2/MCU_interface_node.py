import rclpy
from rclpy.node import Node
from std_msgs.msg import String

import serial

port = serial.Serial(port = 'dev/ttyACM0', baudrate= 9600)

class MCU_interface_node(node):
    def __init__(self):
        super().__init__("MCU_interface_node")
        self.soilCollectionSub = self.create_subscription(String, "soil_collection", self.soilCollectionCB, 10)
        self.vacuumTubeControlSub = self.create_subscription(String, "vacuum_tube_control", self.vacuumTubeCB, 10)
        self.weatherStationSub = self.create_subscription(Empty, "weather_station", self.weatherStationCB, 10)
        self.soilTestingSub = self.creat_subscription(String, "soil_testing", self.soilTestingCB, 10)

    def soilCollectionCB(self, msg):
        port.write(msg.data)
    def vacuumTubeCB(self, msg):
        port.write(msg.data)
    def weatherStationCB(self, msg):
        port.write(msg.data)
    def soilTestingCB(self, msg):
        port.write(msg.data)

def main(args=None):
    rclpy.init(args=args)
    rclpy.spin(MCU_interface_node())
    MCU_interface_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()