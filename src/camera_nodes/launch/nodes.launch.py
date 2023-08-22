from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    common_namespace = "/"

    return LaunchDescription(
        [
            Node(
                package="camera_nodes",
                executable="panorama",
                namespace=common_namespace,
            ),
            Node(
                package="camera_nodes",
                executable="picture",
                namespace=common_namespace,
            ),
            Node(
                package="camera_nodes",
                executable="video",
                namespace=common_namespace,
            ),
        ]
    )
