from launch import LaunchDescription
from launch_ros.actions import Node

# imports for adding launch argument
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    topic_name = LaunchConfiguration("topic_name")
    topic_launch_arg = DeclareLaunchArgument(
        "topic_name", default_value="/usb_cam/image_raw"
    )

    return LaunchDescription(
        [
            topic_launch_arg,
            Node(
                package="usb_cam",
                executable="usb_cam_node_exe",
                parameters=[{"pixel_format": "mjpeg2rgb"}],
                remappings=[("/usb_cam/image_raw", topic_name)]
            ),
        ]
    )
