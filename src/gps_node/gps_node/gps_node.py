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

        # Accept a launch parameter specifying the baud rate of the serial port
        # being connected to
        self.declare_parameter("baud_rate", rclpy.Parameter.Type.INTEGER)
        default_baud_rate = Parameter("baud_rate", rclpy.Parameter.Type.INTEGER, 115200)
        self.baud_rate = self.get_parameter_or("baud_rate", default_baud_rate).value
        self.get_logger().info(f"Using baud rate: {self.baud_rate}")

        # Set a timer to call publish_serial_data() every 0.5 seconds (2Hz).
        timer_period = 0.5
        self.timer = self.create_timer(timer_period, self.publish_serial_data)

    def publish_serial_data(self) -> None:
        """
        Receive and parse serial data containing positioning and rotation
        values from the Arduino, then publish them separately on topics for GPS
        and IMU data.
        """
        with serial.Serial(self.serial_port, self.baud_rate, timeout=1) as ser:
            # read all the data from the serial port until the message is
            # received
            info = ""
            required_data = ["fix", "sats", "lat", "lon"]
#	    required_data = ["fix", "sats", "lat", "lon", "roll", "pitch", "yaw"]
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

            # Extract the data from the serial data, and convert them into ROS
            # messages
            gps_data = self.parse_gps_data(info)
#            imu_data = self.parse_imu_data(info)

            # publish the ros messages
            self.get_logger().info(f"Publishing gps data: {gps_data}")
            self.gps_publisher.publish(gps_data)
#            self.get_logger().info(f"Publishing imu data: {imu_data}")
#            self.imu_publisher.publish(imu_data)

    def parse_imu_data(self, serial_data: str) -> IMU:
        """
        A helper method to parse IMU data read from a serial port, and convert
        it to a ROS message.

        :param serial_data: A string containing the data read from the serial
            port.
        :return: A ROS IMU message (custom defined) containing the extracted IMU data.
        """
        imu_data = IMU()

        # find 'roll' in the data and update the IMU message
        roll_loc = serial_data.find("roll") + 6
        imu_data.roll = float(serial_data[roll_loc : serial_data.find(",", roll_loc)])

        # find 'pitch' in the data and update the IMU message
        pitch_loc = serial_data.find("pitch") + 7
        imu_data.pitch = float(
            serial_data[pitch_loc : serial_data.find(",", pitch_loc)]
        )

        # find 'yaw' in the data and update the IMU message
        yaw_loc = serial_data.find("yaw") + 5
        imu_data.yaw = float(serial_data[yaw_loc : serial_data.find(",", yaw_loc)])

        return imu_data

    def parse_gps_data(self, serial_data: str) -> GPS:
        """
        A helper method to parse GPS data read from a serial port, and convert
        it to a ROS message.

        :param serial_data: A string containing the data read from the serial
            port.
        :return: A ROS GPS message (custom defined) containing the extracted GPS data.
        """
        gps_data = GPS()
        # find 'fix' in the data and update the GPS message
        # (constant is length of 'fix' plus 2 for the ':' and space)
        fix_loc = serial_data.find("fix") + 5
        gps_data.fix = int(serial_data[fix_loc : fix_loc + 1])

        # find 'sats' in the data and update the GPS message
        sat_loc = serial_data.find("sats") + 6
        gps_data.satellites = int(serial_data[sat_loc : serial_data.find(",", sat_loc)])

        # if the GPS doesn't have a fix ignore the latitude and longitude in the data
        if gps_data.fix == 0:
            gps_data.latitude = 0.0
            gps_data.longitude = 0.0
        else:
            # find the latitude and longitude in the data
            lat_end = serial_data.find(",", sat_loc + 2)
            lat = serial_data[serial_data.find("lat:") + 5 : lat_end]
            lon = serial_data[
                serial_data.find("lon:") + 5 : serial_data.find(",", lat_end + 2)
            ]

            # set the sign of the float based on the direction (N vs S and W vs E)
            if "S" in lat:
                gps_data.latitude = -1 * float(lat[: lat.find("S")])
            else:
                gps_data.latitude = float(lat[: lat.find("N")])
            if "W" in lon:
                gps_data.longitude = -1 * float(lon[: lon.find("W")])
            else:
                gps_data.longitude = float(lon[: lon.find("E")])

        return gps_data


def main(args=None):
    rclpy.init(args=args)
    gps_node = GPSNode()
    rclpy.spin(gps_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
