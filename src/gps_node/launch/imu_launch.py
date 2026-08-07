import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    sbg_config_file_arg = DeclareLaunchArgument(
        "sbg_config_file",
        default_value=os.path.join(
            get_package_share_directory("sbg_driver"), "config", "sbg_device_uart_default.yaml"
        ),
        description="Port, baud rate, and enabled logs for the SBG device.",
    )

    sbg_driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory("sbg_driver"), "launch", "sbg_device_launch.py")
        ),
        launch_arguments={"config_file": LaunchConfiguration("sbg_config_file")}.items(),
    )

    imu_bridge = Node(
        package="gps_node",
        executable="imu_node",
        name="imu_node",
        output="screen",
    )

    return LaunchDescription([sbg_config_file_arg, sbg_driver_launch, imu_bridge])