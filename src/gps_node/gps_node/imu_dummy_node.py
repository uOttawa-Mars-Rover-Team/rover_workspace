import rclpy
from rclpy.node import Node
import random

from general_interfaces.msg import IMU

# Rough modifiable test for rover IMU telemetry data in dashboard

class IMUDummyNode(Node):

    def __init__(self, node_name: str = "imu_dummy_node"):
        super().__init__('imu_dummy_node')
        self.publisher_ = self.create_publisher(IMU, 'IMU', 10)
        timer_period = 1
        self.timer = self.create_timer(timer_period, self.timer_callback)

    def timer_callback(self):
        msg = IMU()
        
        # range based on most likely range of values to encounter durign normal operation

        msg.roll = random.uniform(-90.0, 90.0)
        msg.pitch = random.uniform(-40.0, 40.0)
        msg.yaw = random.uniform(0.0, 360.0)
        #msg.heading = random.uniform(0.0, 360.0)

        self.publisher_.publish(msg)
        # self.get_logger().info('Publishing test GPS jitter')

def main(args=None):
    rclpy.init(args=args)
    imu_dummy_node = IMUDummyNode()

    rclpy.spin(imu_dummy_node)

    imu_dummy_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

