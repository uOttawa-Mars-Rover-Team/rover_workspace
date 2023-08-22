from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_device = LaunchConfiguration("serial_device")
    serial_device_launch_arg = DeclareLaunchArgument(
        "serial_device", default_value="/dev/drive_nano"
    )

    return LaunchDescription(
        [
            serial_device_launch_arg,
            Node(
                package="drive_controls",
                executable="simple_drive",
                respawn=True,
                parameters=[{"serial_device": serial_device}],
            ),
        ]
    )
