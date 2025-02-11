from launch_ros.actions import Node
import os
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import LaunchDescription
from moveit_configs_utils.moveit_configs_builder import get_package_share_directory

def generate_launch_description():
    moveit_config = (
            MoveItConfigsBuilder(
                "arm",
                package_name="arm_moveit_config"
                )
            .robot_description(file_path="config/uorover_ik_urdf.urdf.xacro")
            .joint_limits(file_path="config/joint_limits.yaml")
            .trajectory_execution(file_path="config/moveit_controllers.yaml")
            .planning_scene_monitor(
                publish_robot_description=True,
                publish_robot_description_semantic=True
            )
            .planning_pipelines(
                pipelines=["ompl", "pilz_industrial_motion_planner"]
            )
            .to_moveit_configs()
            )
    rviz_config_file = os.path.join(
            get_package_share_directory("arm_moveit_config"),
            "config",
            "moveit.rviz",
            )
    ros2_controllers_path = os.path.join(
            get_package_share_directory("arm_moveit_config"),
            "config",
            "ros2_controllers.yaml",
            )

    run_move_group_node = Node(
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[moveit_config.to_dict()],
            )
    rviz_node = Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="log",
            arguments=["-d", rviz_config_file],
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.robot_description_kinematics,
                moveit_config.planning_pipelines,
                moveit_config.joint_limits,
                ],
            )
    static_tf = Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="static_transform_publisher",
            output="log",
            arguments=["--frame-id", "base_footprint", "--child-frame-id", "L1"],
            )
    robot_state_publisher = Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="both",
            parameters=[moveit_config.robot_description],
            )
    joint_state_broadcaster = Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster"],
            output="screen",
            )
    
    ros2_control_node = Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[ros2_controllers_path],
            remappings=[
                ("/controller_manager/robot_description", "/robot_description"),
                ],
            output="screen",
            )
    uorover_arm_controller_spawner = Node(
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
    uorover_ee_controller_spawner = Node(
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
    peripheral_controller_spawner = Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "peripheral_controller",
                "--controller-manager-timeout",
                "300",
                "--controller-manager",
                "/controller_manager",
                ],
            )

    return LaunchDescription(
            [
                ros2_control_node,
                run_move_group_node,
                rviz_node,
                static_tf,
                robot_state_publisher,
                uorover_arm_controller_spawner,
                uorover_ee_controller_spawner,
                peripheral_controller_spawner,
                joint_state_broadcaster,
            ]
    )