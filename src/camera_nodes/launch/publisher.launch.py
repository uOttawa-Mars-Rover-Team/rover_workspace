from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_name = LaunchConfiguration("camera_name")
    camera_name_launch_arg = DeclareLaunchArgument(
        "camera_name", default_value="usb_cam"
    )
    video_device = LaunchConfiguration("video_device")
    video_device_launch_arg = DeclareLaunchArgument(
        "video_device", default_value="/dev/video0"
    )
    framerate = LaunchConfiguration("framerate")
    framerate_launch_arg = DeclareLaunchArgument("framerate", default_value="30")
    compression_quality = LaunchConfiguration("compression_quality")
    compression_quality_launch_arg = DeclareLaunchArgument(
        "compression_quality", default_value="20"
    )

    return LaunchDescription(
        [
            camera_name_launch_arg,
            video_device_launch_arg,
            framerate_launch_arg,
            compression_quality_launch_arg,
            Node(
                package="camera_nodes",
                executable="publisher",
                parameters=[
                    {
                        "camera_name": camera_name,
                        "video_device": video_device,
                        "framerate": framerate,
                        "compression_quality": compression_quality,
                    }
                ],
            ),
        ]
    )
