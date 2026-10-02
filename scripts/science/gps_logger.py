#!/usr/bin/env python3

import csv
import datetime
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import NavSatFix


class GpsCsvLogger(Node):
    def __init__(self):
        super().__init__("gps_csv_logger")

        # Parameters: Allows you to easily change topic/filename from command line
        self.declare_parameter("topic_name", "/rover/fix")
        self.declare_parameter("output_file", "rover_gps_log.csv")

        topic_name = self.get_parameter("topic_name").get_parameter_value().string_value
        output_file = (
            self.get_parameter("output_file").get_parameter_value().string_value
        )

        # Open file in append/write mode.
        # newline='' prevents extra blank lines in Windows/some Linux configs.
        self.file = open(output_file, mode="w", newline="")
        self.csv_writer = csv.writer(self.file)

        # Write the header row
        self.csv_writer.writerow(
            ["unix_timestamp", "datetime_utc", "latitude", "longitude"]
        )

        # Flush the header to disk immediately
        self.file.flush()
        os.fsync(self.file.fileno())

        # Create the subscriber
        self.subscription = self.create_subscription(
            NavSatFix,
            topic_name,
            self.listener_callback,
            qos_profile=qos_profile_sensor_data,
        )

        self.get_logger().info(f"Subscribed to {topic_name}.")
        self.get_logger().info(
            f"Logging data to {output_file} (Crash resilient mode active)."
        )

    def listener_callback(self, msg):
        # 1. Extract Unix Timestamp from the message header
        sec = msg.header.stamp.sec
        nanosec = msg.header.stamp.nanosec
        unix_timestamp = sec + (nanosec / 1e9)

        # 2. Create an ISO-8601 formatted datetime string (Highly compatible with Pandas/Polars)
        # We use UTC timezone to avoid local time shifts
        dt_obj = datetime.datetime.fromtimestamp(
            unix_timestamp, tz=datetime.timezone.utc
        )
        datetime_utc = dt_obj.isoformat()

        # 3. Extract GPS Data
        lat = msg.latitude
        lon = msg.longitude

        # 4. Write to CSV
        self.csv_writer.writerow([unix_timestamp, datetime_utc, lat, lon])

        # 5. Flush and sync to disk.
        # file.flush() clears python's internal buffer.
        # os.fsync() tells the OS to physically write it to the hard drive immediately.
        self.file.flush()
        os.fsync(self.file.fileno())

    def destroy_node(self):
        # Clean up file on graceful shutdown
        if not self.file.closed:
            self.file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = GpsCsvLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard interrupt, shutting down logger...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
