#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import NavSatFix, NavSatStatus


class SpiralNavSatPublisher(Node):
    def __init__(self):
        super().__init__("spiral_navsat_publisher")

        # Publisher
        self.publisher_ = self.create_publisher(NavSatFix, "/rover/fix", 10)

        # Publish at ~1 Hz
        self.timer = self.create_timer(1.0, self.publish_fix)

        # ------------------------------------------------------------------
        # Spiral configuration
        # ------------------------------------------------------------------

        # Starting coordinate (example: Montreal)
        self.start_lat = 45.5017
        self.start_lon = -73.5673

        # Spiral parameters
        self.theta = 0.0  # Current angle [rad]
        self.theta_step = 0.35  # Angle increment per message
        self.radius_growth_m = 0.75  # Spiral growth [meters/radian]

        # Altitude
        self.altitude_m = 25.0

        self.get_logger().info(
            "Publishing spiral NavSatFix messages on /rover/fix at 1 Hz"
        )

    def publish_fix(self):
        """
        Generate a spiral in local ENU coordinates and convert to lat/lon.
        """

        # Archimedean spiral:
        # r = a * theta
        radius_m = self.radius_growth_m * self.theta

        # Local tangent-plane offsets (meters)
        east_m = radius_m * math.cos(self.theta)
        north_m = radius_m * math.sin(self.theta)

        # Convert local meter offsets to latitude/longitude deltas
        # Approximate Earth conversions:
        #
        # 1 deg latitude  ~= 111320 meters
        # 1 deg longitude ~= 111320 * cos(latitude) meters
        #
        delta_lat = north_m / 111320.0

        delta_lon = east_m / (111320.0 * math.cos(math.radians(self.start_lat)))

        lat = self.start_lat + delta_lat
        lon = self.start_lon + delta_lon

        # Create NavSatFix message
        msg = NavSatFix()

        # Header
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "gps"

        # Status
        msg.status.status = NavSatStatus.STATUS_FIX
        msg.status.service = NavSatStatus.SERVICE_GPS

        # Position
        msg.latitude = lat
        msg.longitude = lon
        msg.altitude = self.altitude_m

        # Example covariance (roughly 1.5m stddev)
        msg.position_covariance = [2.25, 0.0, 0.0, 0.0, 2.25, 0.0, 0.0, 0.0, 4.0]

        msg.position_covariance_type = NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN

        self.publisher_.publish(msg)

        self.get_logger().info(
            f"Published fix: "
            f"lat={lat:.7f}, lon={lon:.7f}, "
            f"radius={radius_m:.2f}m, theta={self.theta:.2f}"
        )

        # Advance spiral
        self.theta += self.theta_step


def main(args=None):
    rclpy.init(args=args)

    node = SpiralNavSatPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
