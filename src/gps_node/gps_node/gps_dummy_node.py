import rclpy
from rclpy.node import Node
import random

from general_interfaces.msg import GPS

# Rough modifiable test for rover icon movement on dashboard nav map

class GPSDummyNode(Node):

    def __init__(self, node_name: str = "gps_dymmy_node"):
        super().__init__('gps_dummy_node')
        self.publisher_ = self.create_publisher(GPS, 'GPS', 10)
        timer_period = 0.1
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        msg = GPS()
        
        msg.fix = 1
        msg.satellites = 12

        # base station coords: lat = 45.42032; lng = -75.68039

        last_dec = random.randint(0, 9)
        lat_random_str = "45.42045" + str(last_dec)
        lat_random = float(lat_random_str)

        msg.latitude = lat_random

        last_dec = random.randint(0, 9)
        lng_random_str = "-75.68075" + str(last_dec)
        lng_random = float(lng_random_str)

        msg.longitude = lng_random

        self.publisher_.publish(msg)
        # self.get_logger().info('Publishing test GPS jitter')

def main(args=None):
    rclpy.init(args=args)
    gps_dummy_node = GPSDummyNode()

    rclpy.spin(gps_dummy_node)

    gps_dummy_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()