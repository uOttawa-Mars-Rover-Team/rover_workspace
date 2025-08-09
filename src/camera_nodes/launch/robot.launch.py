import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    pkg_share = get_package_share_directory('camera_nodes')
    streamer_launch_path = os.path.join(pkg_share, 'launch/srt.launch.py')

    # --- Global Arguments ---
    base_station_ip_arg = DeclareLaunchArgument(
        'base_station_ip', default_value='127.0.0.1', description='IP of the base station'
    )
    
    # --- Camera Definitions ---
    # TO ADD A CAMERA: Just copy and paste one of these blocks and change the arguments.
    
    cam_front_streamer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(streamer_launch_path),
        launch_arguments={
            'camera_name': 'cam_front',
            'video_device': '/dev/video0',
            'base_station_ip': LaunchConfiguration('base_station_ip')
        }.items()
    )
    
    cam_left_streamer = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(streamer_launch_path),
        launch_arguments={
            'camera_name': 'cam_left',
            'video_device': '/dev/video2',
            'base_station_ip': LaunchConfiguration('base_station_ip')
        }.items()
    )
    
    # Add more cameras here...

    return LaunchDescription([
        base_station_ip_arg,
        cam_front_streamer,
        cam_left_streamer,
        # Add other streamers to the list...
    ])
