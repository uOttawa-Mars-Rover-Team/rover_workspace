import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("robotic_arm_description")
    gazebo_share = get_package_share_directory("ros_gz_sim")

    description = xacro.process_file(
        os.path.join(share, "urdf", "arm.urdf.xacro")
    ).toxml()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": "-r -v 3 " + os.path.join(
                share, "config", "arm_world.sdf"
            )
        }.items(),
    )

    robot_state = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": description,
            "use_sim_time": True,
        }],
    )

    clock = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-world", "arm_world",
            "-name", "rover_arm",
            "-topic", "/robot_description",
        ],
    )

    joint_states = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager-timeout", "120",
        ],
    )

    velocity_controller = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=[
            "arm_velocity_controller",
            "--controller-manager-timeout", "120",
        ],
    )

    return LaunchDescription([
        gazebo,
        robot_state,
        clock,
        RegisterEventHandler(
            OnProcessExit(target_action=spawn, on_exit=[joint_states])
        ),
        RegisterEventHandler(
            OnProcessExit(
                target_action=joint_states,
                on_exit=[velocity_controller],
            )
        ),
        spawn,
    ])
