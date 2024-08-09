import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory

from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription


def generate_launch_description():
        
    '''
    # Spacemouse joy
    spacemouse_joy = launch_ros.actions.Node(
            package="joy",
            executable="joy_node",String
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

    # Include arm_servo.launch.py from arm_controls package
    arm_servo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('arm_controls'), 'launch', 'arm_servo.launch.py')
        )
    )
    
    # RViz
    moveit_config = (
            MoveItConfigsBuilder("arm")
            .robot_description(file_path="config/uorover_ik_urdf.urdf.xacro")
            .joint_limits(file_path="config/joint_limits.yaml")
            .to_moveit_configs()
            )
    rviz_config_file = (
            get_package_share_directory("arm_controls")
            + "/config/rviz_config.rviz"
            )
    rviz = launch_ros.actions.Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="log",
            arguments=["-d", rviz_config_file],
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                ],
            )

    return launch.LaunchDescription(
            [
                logitech_joy,
                ik_keyboard_controls,
                ik_joy_controls,
                arm_servo_launch,
                rviz
                ]
            )

