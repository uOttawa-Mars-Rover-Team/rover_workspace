import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
import launch
from launch_ros.actions import Node

def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory('robotic_arm_controls'),
        'config',
        'dual_joystick_xbox_logitech.yaml'
    )

    joy_node_1 = Node(
        package='joy',
        executable='joy_node',
        name='joy_node_controller_1',
        parameters=[{
            'dev': '/dev/input/js0',
            'autorepeat_rate': 50.0,
        }],
        remappings=[('/joy', '/joy/controller_1')],
        output='screen'
    )

    joy_node_2 = Node(
        package='joy',
        executable='joy_node',
        name='joy_node_controller_2',
        parameters=[{
            'dev': '/dev/input/js1',
            'autorepeat_rate': 50.0,
        }],
        remappings=[('/joy', '/joy/controller_2')],
        output='screen'
    )

    controller_node = Node(
        package='robotic_arm_controls',
        executable='dual_joystick_arm_controller',
        name='dual_joystick_arm_controller',
        parameters=[config_file],
        output='screen'
    )

    return launch.LaunchDescription([
        joy_node_1,
        joy_node_2,
        controller_node
    ])