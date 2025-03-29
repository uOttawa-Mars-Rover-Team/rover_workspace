import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution


def generate_launch_description():
    package_name = "autonomous_navigation"
    package_dir = get_package_share_directory(package_name)

    # Config and URDF paths
    pkg_path = os.path.join(package_dir)
    urdf_file = os.path.join(pkg_path, "urdf", "drive_urdf.urdf")
    joy_config_file = os.path.join(
        package_dir,
        "config",
        "f310.config.yaml",
    )
    ekf_config_file = os.path.join(pkg_path, "config", "ekf.yaml")
    rviz_config_file = os.path.join(pkg_path, "rviz", "urdf_config.rviz")
    gazebo_world_file = os.path.join(pkg_path, "world", "smalltown.world")

    # URDF
    robot_description_config = xacro.process_file(urdf_file)

    # Launch configurations
    joy_device_launch_config = LaunchConfiguration(
        "joy_device"
    )  # Joystick device for teleop control

    use_sim_time_launch_config = LaunchConfiguration("use_sim_time")

    rviz_config_launch_config = LaunchConfiguration("rvizconfig")

    # Launch arguments
    joy_device_arg = DeclareLaunchArgument("joy_device", default_value="/dev/input/js2")
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
                "use_sim_time": use_sim_time_launch_config,
            }
        ],
    )

    # Run the spawner node from the gazebo_ros package. The entity name doesn't really matter if you only have a single robot.
    gazebo_spawn_entity_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "rover"],
        output="screen",
    )

    diff_drive_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["diff_cont"]
    )

    joint_broad_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["joint_broad"]
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node_sim",
        parameters=[
            {"dev": joy_device_launch_config, "deadzone": 0.3, "autorepeat_rate": 20.0}
        ],
    )

    teleop_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        name="teleop_twist_joy",
        parameters=[joy_config_file, {"max_speed": 1, "speed_levels": 3}],
        remappings=[("cmd_vel", "diff_cont/cmd_vel_unstamped")],
    )

    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[
            ekf_config_file,
            {"use_sim_time": use_sim_time_launch_config},
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_launch_config],
    )

    # Launch them all!
    return LaunchDescription(
        [
            joy_device_arg,
            use_sim_time_arg,
            rviz_config_arg,
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
            joy_node,
            teleop_node,
            robot_localization_node,
            rviz_node,
        ]
    )
