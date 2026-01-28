import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
import launch
from launch_ros.actions import Node

def generate_launch_description():
    config_file = os.path.join(
        get_package_share_directory('robotic_arm_controls'),
        'config',
        'dual_joystick_xbox_only.yaml'
    )

    joy_node = Node(
    package='joy',
    executable='joy_node',
    name='joy_node_controller_1',
    parameters=[{
        'dev': '/dev/input/by-id/usb-Microsoft_Xbox_Controller-event-joystick',
        'autorepeat_rate': 50.0,
        'deadzone': 0.15
    }],
    remappings=[('/joy', '/joy/controller_1')],
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
        joy_node,
        controller_node
    ])