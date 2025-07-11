import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_path = get_package_share_directory("camera_nodes")

    camera_name = LaunchConfiguration("camera_name")
    camera_name_launch_arg = DeclareLaunchArgument(
        "camera_name", default_value="usb_cam"
    )
    encoding = LaunchConfiguration("encoding")
    encoding_launch_arg = DeclareLaunchArgument("encoding", default_value="libx264")
    bit_rate = LaunchConfiguration("bit_rate")
    bit_rate_launch_arg = DeclareLaunchArgument("bit_rate", default_value="50000")
    qmax = LaunchConfiguration("qmax")
    qmax_launch_arg = DeclareLaunchArgument(
        "qmax",
        default_value="35",
        description="Set max video quantizer scale (VBR). Must be included between -1 and 1024. Higher values result in lower quality but also lower bandwidth usage.",
    )

    ffmpeg_republisher_node = Node(
        package="image_transport",
        executable="republish",
        arguments=["raw", "ffmpeg"],
        parameters=[
            {
                "out.ffmpeg.encoding": encoding,
                "out.ffmpeg.preset": "ultrafast",
                "out.ffmpeg.tune": "zerolatency",
                "out.ffmpeg.bit_rate": bit_rate,
                "out.ffmpeg.qmax": qmax,
            }
        ],
        remappings=[
            ("in", PathJoinSubstitution([camera_name, "image_raw"])),
            (
                "out/ffmpeg",
                PathJoinSubstitution([camera_name, "image_raw", "ffmpeg_out"]),
            ),
        ],
    )

    qos_relay_node = Node(
        package="camera_nodes",
        executable="qos_relay",
        parameters=[
            {
                "input_topic": PathJoinSubstitution(
                    [camera_name, "image_raw", "ffmpeg_out"]
                ),
                "output_topic": PathJoinSubstitution(
                    [camera_name, "image_raw", "ffmpeg"]
                ),
                "qos_profile_name": "SENSOR_DATA",
            }
        ],
    )

    start_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_path,
                "launch",
                "publisher.launch.py",
            )
        ),
        launch_arguments={
            "qos_profile_raw": "SYSTEM_DEFAULT",
            "qos_profile_compressed": "SENSOR_DATA",
        }.items(),
    )

    return LaunchDescription(
        [
            camera_name_launch_arg,
            encoding_launch_arg,
            bit_rate_launch_arg,
            qmax_launch_arg,
            start_publisher_cmd,
            ffmpeg_republisher_node,
            qos_relay_node,
        ]
    )
