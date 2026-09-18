import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory("chassis_controls")
    teleop_joy_params = os.path.join(pkg_path, "config", "f310.config.yaml")

    joy_node = Node(
        package="joy",
        executable="joy_node",
    )
    teleop_twist_joy_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        parameters=[teleop_joy_params],
        remappings=[("cmd_vel", "cmd_vel_teleop")],
    )

    return LaunchDescription(
        [
            joy_node,
            teleop_twist_joy_node,
        ]
    )
