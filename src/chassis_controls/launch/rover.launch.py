import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_path = get_package_share_directory("chassis_controls")
    teleop_joy_params = os.path.join(pkg_path, "config", "f310.config.yaml")
    twist_mux_parameters = os.path.join(pkg_path, "config", "twist_mux.config.yaml")

    use_robot_state_pub = LaunchConfiguration("use_robot_state_pub")
    use_rviz = LaunchConfiguration("use_rviz")

    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
        "use_robot_state_pub",
        default_value="True",
        description="Whether to start the robot state publisher",
    )
    declare_use_rviz_cmd = DeclareLaunchArgument(
        "use_rviz", default_value="False", description="Whether to start Rviz"
    )

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("chassis_controls"),
                    "description",
                    "urdf",
                    "rover.urdf.xacro",
                ]
            ),
        ]
    )

    robot_description = {"robot_description": robot_description_content}

    start_rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                pkg_path,
                "launch",
                "drive_rviz.launch.py",
            )
        ),
        condition=IfCondition(use_rviz),
    )

    start_robot_state_publisher_cmd = Node(
        condition=IfCondition(use_robot_state_pub),
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[robot_description],
        remappings={("/diff_cont/cmd_vel_unstamped", "/cmd_vel")},
    )

    ros2_controllers_path = PathJoinSubstitution(
        [FindPackageShare("chassis_controls"), "config", "rover_ros2_controllers.yaml"]
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[robot_description, ros2_controllers_path],
        output="both",
    )

    diff_cont = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = (
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster, on_exit=[diff_cont]
            )
        )
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
    )
    teleop_twist_joy_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        parameters=[teleop_joy_params],
        remappings=[("cmd_vel", "cmd_vel_joy")],
    )
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        remappings={("/cmd_vel_out", "/diff_cont/cmd_vel_unstamped")},
        parameters=[twist_mux_parameters],
    )

    return LaunchDescription(
        [
            declare_use_robot_state_pub_cmd,
            declare_use_rviz_cmd,
            ros2_control_node,
            start_rviz_cmd,
            start_robot_state_publisher_cmd,
            joint_state_broadcaster,
            delay_robot_controller_spawner_after_joint_state_broadcaster_spawner,
            joy_node,
            teleop_twist_joy_node,
            twist_mux,
        ]
        # ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/diff_cont/cmd_vel_unstamped
    )
