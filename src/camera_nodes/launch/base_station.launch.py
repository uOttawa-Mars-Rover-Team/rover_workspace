import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess

def generate_launch_description():
    pkg_share = get_package_share_directory('camera_nodes')
    base_config_path = os.path.join(pkg_share, 'config/base_station_mediamtx.yml')

    # This launch file ONLY starts the mediamtx server.
    base_mediamtx_server = ExecuteProcess(
        cmd=['mediamtx', base_config_path],
        name='base_mediamtx_server',
        output='screen'
    )

    return LaunchDescription([
        base_mediamtx_server,
    ])
