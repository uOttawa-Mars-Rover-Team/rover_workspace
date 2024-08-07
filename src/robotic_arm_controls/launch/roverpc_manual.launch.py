import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory


def generate_launch_description():

    # Router node
    m_router = launch_ros.actions.Node(
            package="robotic_arm_controls",
            executable="m_router",
            parameters=[
                {'timeout_delay': 0.1},
                {'serial_dev': "/dev/ttyACM0"},
                {'baudrate': 500000}
            ],
            output="screen",
            )

    return launch.LaunchDescription(
            [
                m_router
                ]
            )

