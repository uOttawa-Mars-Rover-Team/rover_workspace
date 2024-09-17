# From:
# https://github.com/ros-navigation/navigation2_tutorials/blob/8d80918b0e926b02758379bffbd6291fec434327/nav2_gps_waypoint_follower_demo/launch/dual_ekf_navsat.launch.py

import os

from ament_index_python import get_package_share_directory
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_path = os.path.join(get_package_share_directory("autonomous_navigation"))

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation (Gazebo) clock if true",
    )
    ekf_config_file = os.path.join(pkg_path, "config/dual_ekf_navsat.yaml")

    return LaunchDescription(
        [
            declare_use_sim_time_cmd,
            Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node_odom",
                output="screen",
                parameters=[
                    ekf_config_file,
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                ],
                remappings=[("odometry/filtered", "odometry/local")],
            ),
            Node(
                package="robot_localization",
                executable="ekf_node",
                name="ekf_filter_node_map",
                output="screen",
                parameters=[
                    ekf_config_file,
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                ],
                remappings=[("odometry/filtered", "odometry/global")],
            ),
            Node(
                package="robot_localization",
                executable="navsat_transform_node",
                name="navsat_transform",
                output="screen",
                parameters=[
                    ekf_config_file,
                    {"use_sim_time": LaunchConfiguration("use_sim_time")},
                ],
                remappings=[
                    ("imu", "imu/data"),
                    ("gps/fix", "gps/fix"),
                    ("gps/filtered", "gps/filtered"),
                    ("odometry/gps", "odometry/gps"),
                    ("odometry/filtered", "odometry/global"),
                ],
            ),
        ]
    )
