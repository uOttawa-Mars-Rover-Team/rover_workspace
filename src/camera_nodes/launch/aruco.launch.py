from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import LaunchConfigurationEquals, LaunchConfigurationNotEquals

# imports for generating launch description by calling cam.launch file
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    image_topic = LaunchConfiguration("image_topic")
    image_topic_arg = DeclareLaunchArgument(
        "image_topic",
        default_value="",
        description='The image topic that the aruco detection will subscribe to. Leave this blank to automatically startup a new image node under the "aruco_cam" namespace.',
    )
    is_compressed = LaunchConfiguration("is_compressed")
    is_compressed_arg = DeclareLaunchArgument(
        "is_compressed",
        default_value="False",
        description="When the `image_topic` param is provided, whether the image_topic being subscribed to publishes compressed images.",
    )
    is_ffmpeg = LaunchConfiguration("is_ffmpeg")
    is_ffmpeg_arg = DeclareLaunchArgument(
        "is_ffmpeg",
        default_value="False",
        description="When the `image_topic` param is provided, whether the image_topic being subscribed to publishes FFMPEG packets.",
    )

    return LaunchDescription(
        [
            image_topic_arg,
            is_compressed_arg,
            is_ffmpeg_arg,
            GroupAction(
                condition=LaunchConfigurationEquals("image_topic", ""),
                actions=[
                    Node(
                        package="usb_cam",
                        executable="usb_cam_node_exe",
                        parameters=[{"pixel_format": "mjpeg2rgb"}],
                        namespace="aruco_cam",
                    ),
                    Node(
                        package="camera_nodes",
                        executable="aruco",
                        parameters=[
                            {
                                "image_topic": "aruco_cam/image_raw/compressed",
                                "is_compressed": True,
                            }
                        ],
                    ),
                ],
            ),
            GroupAction(
                condition=LaunchConfigurationNotEquals("image_topic", ""),
                actions=[
                    Node(
                        package="camera_nodes",
                        executable="aruco",
                        parameters=[
                            {
                                "image_topic": image_topic,
                                "is_compressed": is_compressed,
                                "is_ffmpeg": is_ffmpeg,
                            }
                        ],
                    ),
                ],
            ),
        ]
    )
