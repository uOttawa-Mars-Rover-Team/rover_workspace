from datetime import timedelta
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # --- Argument for this single instance ---
    camera_name_arg = DeclareLaunchArgument('camera_name', default_value='usb_cam', description='The unique name of the camera (e.g., cam_front)')

    return LaunchDescription([
        camera_name_arg,
        Node(
            package='gscam',
            executable='gscam_node',
            name=['gscam_', LaunchConfiguration('camera_name')],
            namespace=LaunchConfiguration('camera_name'), # Use camera_name for the ROS namespace
            parameters=[{
                'gscam_config': [
                    'rtspsrc location=rtsp://localhost:8554/', LaunchConfiguration('camera_name'), # Use camera_name for the path
                    ' protocols=tcp latency=0 drop-on-latency=true buffer-mode=0 ! application/x-rtp,media=video ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert'
                ]
            }],
            respawn=True,
            respawn_delay=timedelta(seconds=3)
        )
    ])
