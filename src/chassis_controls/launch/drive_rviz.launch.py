from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("chassis_controls"), "config", "drive.rviz"]
    )

    start_rviz_cmd = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config_file],
        output="screen",
    )

    return LaunchDescription(
        [
            start_rviz_cmd,
        ]
    )
