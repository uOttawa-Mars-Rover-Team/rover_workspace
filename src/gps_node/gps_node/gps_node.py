#!/usr/bin/env python

import rclpy
import serial
from rclpy.node import Node
from rclpy.parameter import Parameter

from general_interfaces.msg import GPS, IMU


class GPSNode(Node):
    """
    This node is responsible for parsing the incoming GPS and IMU data that the
    Arduino sends via serial port with all the values read from the sensors.
    This node puts that data into messages and publishes them to ROS topics.
    The GPS data is put in the GPS.msg message and published under the /GPS
    topic. The IMU data is put in the IMU.msg message and published under the
    /IMU topic. The definitions for both message types exist in the
    `general_interfaces` package.
    """

    def __init__(self, node_name: str = "gps_node"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Startup publishers for the IMU and GPS messages
        self.gps_publisher = self.create_publisher(GPS, "GPS", 10)
        self.get_logger().info(
            f"Publishing messages at: {self.gps_publisher.topic_name}"
        )
        self.imu_publisher = self.create_publisher(IMU, "IMU", 10)
        self.get_logger().info(
            f"Publishing messages at: {self.imu_publisher.topic_name}"
        )

        # Accept a launch parameter specifying the serial port on which the
        # Arduino is connected to
        self.declare_parameter("serial_port", rclpy.Parameter.Type.STRING)
        default_serial_port = Parameter(
            "serial_port", rclpy.Parameter.Type.STRING, "/dev/ttyACM0"
        )
        self.serial_port = self.get_parameter_or(
            "serial_port", default_serial_port
        ).value
        self.get_logger().info(f"Using serial port: {self.serial_port}")

        # Set a timer to call publish_serial_data() every 0.5 seconds (2Hz).
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.publish_serial_data)

    def publish_serial_data(self) -> None:
        """
        Receive and parse serial data containing positioning and rotation
        values from the Arduino, then publish them separately on topics for GPS
        and IMU data.
        """
        with serial.Serial(self.serial_port, 115200, timeout=1) as ser:
            # read all the data from the serial port until the message is
            # received
            info = ""
            required_data = ["fix", "sats", "lat", "lon", "roll", "pitch", "yaw"]
            missing_data = True

            while missing_data:
                # read from the port(data entries should be separated by
                # newlines)
                info = info + ser.readline().decode("utf-8")

                # check if all the data for this cycle has been received
                missing_data = False
                for data_entry in required_data:
                    if data_entry not in info:
                        missing_data = True

            # make the messages
            gps_data = GPS()
            imu_data = IMU()

            # find 'fix' in the data and update the GPS message
            # (constant is length of 'fix' plus 2 for the ':' and space)
            fix_loc = info.find("fix") + 5
            gps_data.fix = int(info[fix_loc : fix_loc + 1])

            # find 'sats' in the data and update the GPS message
            sat_loc = info.find("sats") + 6
            gps_data.satellites = int(info[sat_loc : info.find(",", sat_loc)])

            # if the GPS doesn't have a fix ignore the latitude and longitude in the data
            if gps_data.fix == 0:
                gps_data.latitude = 0.0
                gps_data.longitude = 0.0
            else:
                # find the latitude and longitude in the data
                lat_end = info.find(",", sat_loc + 2)
                lat = info[info.find("lat:") + 5 : lat_end]
                lon = info[info.find("lon:") + 5 : info.find(",", lat_end + 2)]

                # set the sign of the float based on the direction (N vs S and W vs E)
                if "S" in lat:
                    gps_data.latitude = -1 * float(lat[: lat.find("S")])
                else:
                    gps_data.latitude = float(lat[: lat.find("N")])
                if "W" in lon:
                    gps_data.longitude = -1 * float(lon[: lon.find("W")])
                else:
                    gps_data.longitude = float(lon[: lon.find("E")])

            # find 'roll' in the data and update the IMU message
            roll_loc = info.find("roll") + 6
            imu_data.roll = float(info[roll_loc : info.find(",", roll_loc)])

            # find 'pitch' in the data and update the IMU message
            pitch_loc = info.find("pitch") + 7
            imu_data.pitch = float(info[pitch_loc : info.find(",", pitch_loc)])

            # find 'yaw' in the data and update the IMU message
            yaw_loc = info.find("yaw") + 5
            imu_data.yaw = float(info[yaw_loc : info.find(",", yaw_loc)])

            # publish the ros messages
            self.get_logger().info(f"Publishing gps data: {gps_data}")
            self.gps_publisher.publish(gps_data)
            self.get_logger().info(f"Publishing imu data: {imu_data}")
            self.imu_publisher.publish(imu_data)


def main(args=None):
    rclpy.init(args=args)
    gps_node = GPSNode()
    rclpy.spin(gps_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
