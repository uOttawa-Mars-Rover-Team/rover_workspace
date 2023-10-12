from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    image_topic = LaunchConfiguration("image_topic")
    image_topic_launch_arg = DeclareLaunchArgument(
        "image_topic", default_value="/drive_cam/image_raw"
    )

    return LaunchDescription(
        [
            image_topic_launch_arg,
            Node(
                package="camera_nodes",
                executable="aruco",
                parameters=[{"image_topic": image_topic}],
            ),
        ]
    )
