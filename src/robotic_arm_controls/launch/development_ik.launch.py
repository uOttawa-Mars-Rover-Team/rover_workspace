import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory


def generate_launch_description():
        
    '''
    # Spacemouse joy
    spacemouse_joy = launch_ros.actions.Node(
            package="joy",
            executable="joy_node",
            parameters=[
                {'dev': '/dev/input/arm_spacemouse'}
            ],
            remappings=[
                ("/joy", "/joy/arm_cmd"),
                ],
            output="screen",
            )'''

    # Logitech joy
    logitech_joy = launch_ros.actions.Node(
            package="joy",
            executable="joy_node",
            parameters=[
                {'dev': '/dev/input/arm_logitech'}
            ],
            remappings=[
                ("/joy", "/joy/arm_cmd"),
                ],
            output="screen",
            )
            
    # Keyboard
    ik_keyboard_controls = launch_ros.actions.Node(
            package="robotic_arm_controls",
            executable="ik_keyboard_controls",
            output="screen",
            )

    # Joy IK Controller
    ik_joy_controls = launch_ros.actions.Node(
            package="robotic_arm_controls",
            executable="ik_joy_controls",
            parameters=[
                {'deadzone': 0.4},
                {'pub_rate': 20.0}
            ],
            output="screen",
            )

    return launch.LaunchDescription(
            [
                logitech_joy,
                ik_keyboard_controls,
                ik_joy_controls
                ]
            )

