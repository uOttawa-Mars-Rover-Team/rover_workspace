from ament_index_python.packages import get_package_share_directory, get_package_share_path
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch.substitutions import FindExecutable, LaunchConfiguration, Command, PathJoinSubstitution
from launch.actions import DeclareLaunchArgument, RegisterEventHandler
from launch_ros.substitutions import FindPackageShare
from launch.event_handlers import OnProcessExit
import xacro
import os

def generate_launch_description():

    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_rviz = LaunchConfiguration('use_rviz')

    declare_use_rviz_cmd = DeclareLaunchArgument(
            'use_rviz',
            default_value='True',
            description='Whether to start Rviz')

    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
            'use_robot_state_pub',
            default_value='True',
            description='Whether to start the robot state publisher')

    rviz_config_file = PathJoinSubstitution([
                FindPackageShare("chassis_controls"),
                "config",
                "drive.rviz"])

    robot_description_content = Command([
                PathJoinSubstitution([FindExecutable(name="xacro")]),
                " ",
                PathJoinSubstitution([
                        FindPackageShare("chassis_controls"),
                        "description",
                        "urdf",
                        "rover.urdf.xacro"])])

    robot_description = {"robot_description": robot_description_content}

    start_robot_state_publisher_cmd = Node(
        condition=IfCondition(use_robot_state_pub),
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        #arguments=[str(urdf_path)],
        parameters=[robot_description],
        remappings={
            ("/diff_cont/cmd_vel_unstamped", "/cmd_vel")})

    rviz_cmd = Node(
        condition=IfCondition(use_rviz),
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_file],
        output='screen')

    static_tf = Node(
            package="tf2_ros",
            executable="static_transform_publisher",
            name="static_transform_publisher",
            output="log")

    ros2_controllers_path = PathJoinSubstitution([
            FindPackageShare("chassis_controls"),
            "config",
            "rover_ros2_controllers.yaml"])

    ros2_control_node = Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[robot_description,ros2_controllers_path],
            output="both")

    diff_cont = Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diff_cont", "--controller-manager", "/controller_manager"],
            output="screen")

    joint_state_broadcaster = Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
            output="screen")

    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster,
            on_exit=[diff_cont]))

    return LaunchDescription(
            [
                declare_use_robot_state_pub_cmd,
                declare_use_rviz_cmd,

                ros2_control_node,
                rviz_cmd,
                static_tf,
                start_robot_state_publisher_cmd,
                joint_state_broadcaster,
                delay_robot_controller_spawner_after_joint_state_broadcaster_spawner
            ]
            # ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
            )
