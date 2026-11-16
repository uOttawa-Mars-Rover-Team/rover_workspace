"""Launch the five-joint arm simulation with team controls."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("robotic_arm_description")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(share, "launch", "development_gazebo.launch.py")
        )
    )

    bridge = Node(
        package="robotic_arm_controls",
        executable="sim_command_bridge",
        output="screen",
        parameters=[{
            # Provisional: L1 -> shoulder, L2 -> elbow.
            # EE is omitted because gripper articulation is not modeled.
            "output_indices": [0, 1, 2, 3, 4],
            "command_timeout": 0.3,
        }],
    )

    controls = Node(
        package="robotic_arm_controls",
        executable="integrative_control",
        output="screen",
        parameters=[{"simulation_stream_commands": True}],
    )

    return LaunchDescription([gazebo, bridge, controls])
