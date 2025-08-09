from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ld_sensor_array',
            executable='sensor_array_interface',
            name='sensor_array_interface'
        ),
        Node(
            package='ld_sensor_array',
            executable='sensor_array_viewer',
            name='sensor_array_viewer'
        ),
    ])