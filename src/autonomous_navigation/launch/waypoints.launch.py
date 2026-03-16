# Modified/Inspired from:
# https://github.com/ros-navigation/navigation2_tutorials/blob/8d80918b0e926b02758379bffbd6291fec434327/nav2_gps_waypoint_follower_demo/launch/gps_waypoint_follower.launch.py

import os

import xacro
from ament_index_python import get_package_share_directory
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from nav2_common.launch import RewrittenYaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import SetParameter


def generate_launch_description():
    pkg_path = os.path.join(get_package_share_directory("autonomous_navigation"))

    urdf_file = os.path.join(pkg_path, "urdf", "ab1", "robot.urdf.xacro")
    robot_description_config = xacro.process_file(urdf_file)
    gazebo_world_file = os.path.join(pkg_path, "world/obstacles.world")
    rviz_config_file = os.path.join(pkg_path, "rviz/nav2_config.rviz")
    nav2_params = os.path.join(pkg_path, "config/nav2_no_map_params.yaml")
    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )

    use_sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="True",
        description="Flag for node to follow sim clock",
    )
    rviz_config_arg = DeclareLaunchArgument(
        name="rvizconfig",
        default_value=rviz_config_file,
        description="Absolute path to rviz config file",
    )
    # Create a robot_state_publisher node
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description_config.toxml(),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }
        ],
    )
    joint_broad_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["joint_broad"]
    )
    diff_drive_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["diff_cont"]
    )
    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    gazebo_spawn_entity_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "rover"],
        output="screen",
    )
    robot_localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_path, "gps_navsat.launch.py")),
        launch_arguments={"use_sim_time": LaunchConfiguration("use_sim_time")}.items(),
    )
    navigation2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_path, "navigation.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file": configured_params,
            "autostart": "True",
        }.items(),
    )
    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("nav2_bringup"), "launch", "rviz_launch.py"
            )
        ),
        launch_arguments={"rviz_config": rviz_config_file}.items(),
    )

    return LaunchDescription(
        [
            use_sim_time_arg,
            SetParameter(
                name="use_sim_time",
                value=LaunchConfiguration("use_sim_time")
            ),
            rviz_config_arg,
            navigation2_cmd,
            rviz_cmd,
            robot_localization_cmd,
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        PathJoinSubstitution(
                            [
                                FindPackageShare("gazebo_ros"),
                                "launch",
                                "gzserver.launch.py",
                            ]
                        )
                    ]
                ),
                launch_arguments={
                    "world": gazebo_world_file,
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    [
                        PathJoinSubstitution(
                            [
                                FindPackageShare("gazebo_ros"),
                                "launch",
                                "gzclient.launch.py",
                            ]
                        )
                    ]
                )
            ),
            robot_state_publisher_node,
            gazebo_spawn_entity_node,
            diff_drive_spawner,
            joint_broad_spawner,
        ]
    )
