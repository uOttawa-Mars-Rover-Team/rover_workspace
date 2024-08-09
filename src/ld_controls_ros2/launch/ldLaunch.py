from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='keyboard',
            executable='keyboard',
            name='keyboard'
        ),
        Node(
            package='ld_controls_ros2',
            executable='MCU',
            name='MCU'
        ),
    ])