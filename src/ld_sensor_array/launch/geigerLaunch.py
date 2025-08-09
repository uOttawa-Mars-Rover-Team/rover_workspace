from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ld_sensor_array',
            executable='geiger_publisher',
            name='geiger_publisher'
        ),
        Node(
            package='ld_sensor_array',
            executable='geiger_viewer',
            name='geiger_viewer'
        ),
    ])