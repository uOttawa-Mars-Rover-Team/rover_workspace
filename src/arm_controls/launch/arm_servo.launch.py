import os
import launch
import launch_ros

from ament_index_python.packages import get_package_share_directory
from launch_param_builder import ParameterBuilder

from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory


def generate_launch_description():
    moveit_config = (
            MoveItConfigsBuilder("arm")
            .robot_description(file_path="config/uorover_ik_urdf.urdf.xacro")
            .joint_limits(file_path="config/joint_limits.yaml")
            .to_moveit_configs()
            )

    servo_params = {
            "moveit_servo": ParameterBuilder("arm_controls")
            .yaml("config/arm_servo.yaml")
            .to_dict()
            }

    acceleration_filter_update_period = {"update_period": 0.05}
    planning_group_name = {"planning_group_name": "uorover_arm"}

    rviz_config_file = (
            get_package_share_directory("arm_controls")
            + "/config/rviz_config.rviz"
            )
    rviz_node = launch_ros.actions.Node(
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

    ros2_controllers_path = os.path.join(
            get_package_share_directory("arm_moveit_config"),
            "config",
            "ros2_controllers.yaml",
            )
    ros2_control_node = launch_ros.actions.Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[ros2_controllers_path],
            remappings=[
                ("/controller_manager/robot_description", "/robot_description"),
                ],
            output="screen",
            )

    joint_state_broadcaster_spawner = launch_ros.actions.Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "joint_state_broadcaster",
                "--controller-manager-timeout",
                "300",
                "--controller-manager",
                "/controller_manager",
                ]
            )

    uorover_arm_controller_spawner = launch_ros.actions.Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "uorover_arm_controller",
                "--controller-manager-timeout",
                "300",
                "--controller-manager",
                "/controller_manager",
                ],
            )

    uorover_ee_controller_spawner = launch_ros.actions.Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "uorover_ee_controller",
                "--controller-manager-timeout",
                "300",
                "--controller-manager",
                "/controller_manager",
                ],
            )
    # Launch as much as possible in components
    container = launch_ros.actions.ComposableNodeContainer(
        name="moveit_servo_demo_container",
        namespace="/",
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=[
            launch_ros.descriptions.ComposableNode(
                package="moveit_servo",
                plugin="moveit_servo::ServoNode",
                name="servo_node",
                parameters=[
                    servo_params,
                    acceleration_filter_update_period,
                    planning_group_name,
                    moveit_config.robot_description,
                    moveit_config.robot_description_semantic,
                    moveit_config.robot_description_kinematics,
                    moveit_config.joint_limits,
                ],
            ),
            launch_ros.descriptions.ComposableNode(
                package="robot_state_publisher",
                plugin="robot_state_publisher::RobotStatePublisher",
                name="robot_state_publisher",
                parameters=[moveit_config.robot_description],
            ),
            launch_ros.descriptions.ComposableNode(
                package="tf2_ros",
                plugin="tf2_ros::StaticTransformBroadcasterNode",
                name="static_tf2_broadcaster",
                parameters=[{"child_frame_id": "/base_footprint", "frame_id": "/world"}],
            ),
        ],
        output="screen",
    )

    return launch.LaunchDescription(
            [
                rviz_node,
                ros2_control_node,
                joint_state_broadcaster_spawner,
                uorover_arm_controller_spawner,
                uorover_ee_controller_spawner,
                container,
                ]
            )

