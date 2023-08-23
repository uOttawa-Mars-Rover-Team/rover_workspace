import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    joy_config = LaunchConfiguration("joy_config")
    joy_config_launch_arg = DeclareLaunchArgument("joy_config", default_value="f310")

    joy_device = LaunchConfiguration("joy_device")
    joy_device_launch_arg = DeclareLaunchArgument(
        "joy_device", default_value="/dev/input/js2"
    )

    return LaunchDescription(
        [
            joy_config_launch_arg,
            joy_device_launch_arg,
            Node(
                package="joy",
                executable="joy_node",
                name="joy_node",
                parameters=[
                    {"dev": joy_device, "deadzone": 0.3, "autorepeat_rate": 20.0}
                ],
            ),
            Node(
                package="teleop_twist_joy",
                executable="teleop_node",
                name="teleop_twist_joy",
                parameters=[
                    [
                        os.path.join(
                            get_package_share_directory("drive_controls"), "config", ""
                        ),
                        joy_config,
                        ".config.yaml",
                    ],
                    {"max_speed": 1, "speed_levels": 3},
                ],
            ),
            Node(
                package="drive_controls",
                executable="cmd_vel_mux",
                name="cmd_vel_mux",
                parameters=[
                    {"block_duration": 5},
                ],
                remappings=[("cmd_vel", "turtle1/cmd_vel")],
            ),
            Node(package="turtlesim", executable="turtlesim_node", name="sim"),
        ]
    )
