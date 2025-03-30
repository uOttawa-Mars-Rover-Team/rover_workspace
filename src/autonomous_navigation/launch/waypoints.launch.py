# Modified/Inspired from:
# https://github.com/ros-navigation/navigation2_tutorials/blob/8d80918b0e926b02758379bffbd6291fec434327/nav2_gps_waypoint_follower_demo/launch/gps_waypoint_follower.launch.py

import os

from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_path = os.path.join(get_package_share_directory("autonomous_navigation"))

    urdf_file = os.path.join(pkg_path, "urdf", "ab1", "robot.urdf.xacro")
    gazebo_world_file = os.path.join(pkg_path, "world", "obstacles.world")
    rviz_config_file = os.path.join(pkg_path, "rviz", "nav2_config.rviz")
    nav2_params = os.path.join(pkg_path, "config", "nav2_no_map_params.yaml")
    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )

    # launch configurations
    use_sim_time_launch_config = LaunchConfiguration("use_sim_time")

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

    gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_path, "gazebo.launch.py")
        ),
        launch_arguments={
            "use_sim_time": use_sim_time_launch_config,
            "robot_description_file": urdf_file,
            "gazebo_world_file": gazebo_world_file,
        }.items(),
    )

    robot_localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_path, "gps_navsat.launch.py")),
        launch_arguments={"use_sim_time": use_sim_time_launch_config}.items(),
    )
    navigation2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_path, "navigation.launch.py")),
        launch_arguments={
            "use_sim_time": use_sim_time_launch_config,
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
            rviz_config_arg,
            navigation2_cmd,
            rviz_cmd,
            robot_localization_cmd,
            gazebo_cmd,
        ]
    )
