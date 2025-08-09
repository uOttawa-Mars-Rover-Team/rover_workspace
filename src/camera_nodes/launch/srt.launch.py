from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # --- Arguments for this single instance ---
    camera_name_arg = DeclareLaunchArgument('camera_name', default_value='usb_cam', description='The unique name of the camera (e.g., cam_front)')
    video_device_arg = DeclareLaunchArgument('video_device', default_value='/dev/video0', description='The device file of the camera (e.g., /dev/video0)')
    base_station_ip_arg = DeclareLaunchArgument('base_station_ip', default_value='127.0.0.1', description='IP of the base station')
    bitrate_arg = DeclareLaunchArgument('bitrate', default_value='200k', description='FFmpeg bitrate argument')
    fps_arg = DeclareLaunchArgument('fps', default_value='15', description='FPS (frames per second)')

    return LaunchDescription([
        camera_name_arg,
        video_device_arg,
        base_station_ip_arg,
        bitrate_arg,
        fps_arg,

        ExecuteProcess(
            cmd=[
                'ffmpeg', '-f', 'v4l2', '-input_format', 'mjpeg', '-i', LaunchConfiguration('video_device'),
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'ultrafast',
                '-tune', 'zerolatency', '-b:v', LaunchConfiguration('bitrate'), '-r', LaunchConfiguration('fps'), '-g', LaunchConfiguration('fps'), # Low-latency GOP size
                '-f', 'mpegts',
                [
                    'srt://', LaunchConfiguration('base_station_ip'), ':9000?streamid=publish:',
                    LaunchConfiguration('camera_name'), # Use the camera_name argument
                    '&mode=caller&latency=20000' # Low-latency SRT options
                ]
            ],
            name=['ffmpeg_', LaunchConfiguration('camera_name')],
            output='screen'
        )
    ])
