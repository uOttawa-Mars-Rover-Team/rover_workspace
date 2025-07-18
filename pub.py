import rclpy
from rclpy.node import Node
from nav_msgs.msg import OccupancyGrid
import numpy as np
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy


class MockMapPublisher(Node):
    def __init__(self):
        super().__init__("mock_map_publisher")

        # Define QoS profile with matching settings for the subscribers
        qos_profile = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )

        # Create publisher with custom QoS
        self.publisher = self.create_publisher(OccupancyGrid, "/map", qos_profile)

        # Mock map dimensions (e.g., 10x10 grid)
        self.width = 20 * 40
        self.height = 20 * 40
        self.resolution = 0.05  # in meters per cell

        # Create an empty map (100 cells)
        self.map_data = np.zeros(self.width * self.height, dtype=int)

        # Set some cells to "occupied" (1)
        self.map_data[5] = 100  # Example: setting a cell as occupied

        # Create and publish the map periodically
        self.timer = self.create_timer(1.0, self.timer_callback)

    def timer_callback(self):
        msg = OccupancyGrid()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "map"
        msg.info.width = self.width
        msg.info.height = self.height
        msg.info.resolution = self.resolution
        msg.info.origin.position.x = -20.0
        msg.info.origin.position.y = -20.0
        msg.data = self.map_data.tolist()
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    mock_map_publisher = MockMapPublisher()
    rclpy.spin(mock_map_publisher)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
