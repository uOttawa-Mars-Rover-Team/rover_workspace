import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sbg_driver.msg import SbgImuData, SbgEkfQuat
from general_interfaces.msg import IMU


def quaternion_to_roll_pitch(w: float, x: float, y: float, z: float):
    """ZYX (aerospace) convention roll/pitch extraction, in radians."""
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    sin_pitch = max(-1.0, min(1.0, 2.0 * (w * y - z * x)))
    pitch = math.asin(sin_pitch)
    return roll, pitch


class ImuNode(Node):
    """Bridges sbg_ros2_driver topics into the dashboard's IMU message contract."""

    def __init__(self):
        super().__init__("imu_node")

        self.declare_parameter("output_topic", "/imu/telemetry")
        self.declare_parameter("sbg_imu_data_topic", "/sbg/imu_data")
        self.declare_parameter("sbg_ekf_quat_topic", "/sbg/ekf_quat")

        output_topic = self.get_parameter("output_topic").value
        imu_data_topic = self.get_parameter("sbg_imu_data_topic").value
        ekf_quat_topic = self.get_parameter("sbg_ekf_quat_topic").value

        self._publisher = self.create_publisher(IMU, output_topic, 10)
        self._latest_accel = None  # (x, y, z) m/s^2, filled by SbgImuData

        self.create_subscription(
            SbgImuData, imu_data_topic, self._on_imu_data, qos_profile_sensor_data
        )
        self.create_subscription(
            SbgEkfQuat, ekf_quat_topic, self._on_ekf_quat, qos_profile_sensor_data
        )

        self.get_logger().info(
            f"imu_node: bridging '{imu_data_topic}' + '{ekf_quat_topic}' -> '{output_topic}'"
        )

    def _on_imu_data(self, msg: SbgImuData):
        self._latest_accel = (msg.accel.x, msg.accel.y, msg.accel.z)

    def _on_ekf_quat(self, msg: SbgEkfQuat):
        if self._latest_accel is None:
            return  # wait for at least one accelerometer sample

        q = msg.quaternion
        roll, pitch = quaternion_to_roll_pitch(q.w, q.x, q.y, q.z)
        ax, ay, az = self._latest_accel
        norm = math.sqrt(ax * ax + ay * ay + az * az)

        out = IMU()
        out.roll = math.degrees(roll)
        out.pitch = math.degrees(pitch)
        out.accel_x = ax
        out.accel_y = ay
        out.accel_z = az
        out.accel_norm = norm

        self._publisher.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()