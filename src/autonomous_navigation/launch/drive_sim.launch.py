import os

from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


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

    gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, "gazebo.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time_launch_config,
            "roboto_description_file": urdf_file,
            "gazebo_world_file": gazebo_world_file,
        }.items(),
    )

    # Launch them all!
    return LaunchDescription(
        [
            joy_device_arg,
            use_sim_time_arg,
            rviz_config_arg,
            gazebo_cmd,
            joy_node,
            teleop_node,
            robot_localization_node,
            rviz_node,
        ]
    )
