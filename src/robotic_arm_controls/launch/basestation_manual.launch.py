import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory


def generate_launch_description():

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
            
    # Toggler node
    m_toggler = launch_ros.actions.Node(
            package="robotic_arm_controls",
            executable="m_toggler",
            output="screen",
            )

    # Manual controls
    m_arm_controls = launch_ros.actions.Node(
            package="robotic_arm_controls",
            executable="m_arm_controls",
            output="screen",
            )

    return launch.LaunchDescription(
            [
                logitech_joy,
                m_toggler,
                m_arm_controls
                ]
            )

