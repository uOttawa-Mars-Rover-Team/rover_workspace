import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    autonomous_navigation_package = get_package_share_directory("autonomous_navigation")
    chassis_controls_package = get_package_share_directory("chassis_controls")

    rviz_config_file = os.path.join(
        autonomous_navigation_package, "rviz/nav2_config.rviz"
    )
    nav2_params = os.path.join(autonomous_navigation_package, "config/nav2_params.yaml")
    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )
    slam_toolbox_params = os.path.join(
        autonomous_navigation_package,
        "config",
        "mapper_params_online_async.yaml",
    )
    declare_use_rviz_cmd = DeclareLaunchArgument(
        "use_rviz", default_value="True", description="Whether to start Rviz"
    )
    use_rviz = LaunchConfiguration("use_rviz")

    drive_system = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(chassis_controls_package, "launch", "rover.launch.py")
        ),
        launch_arguments={
            "use_rviz": "False",
        }.items(),
    )
    localization_system = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                autonomous_navigation_package, "launch", "gps_navsat.launch.py"
            )
        ),
        launch_arguments={
            "use_rviz": "False",
        }.items(),
    )

    rviz_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("nav2_bringup"), "launch", "rviz_launch.py"
            )
        ),
        launch_arguments={"rviz_config": rviz_config_file}.items(),
        condition=IfCondition(use_rviz),
    )

    imu_launch_file = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("tm_imu"), "launch", "imu.launch.py"
            )
        ),
    )
    lidar_launch_file = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("rplidar_ros"),
                "launch",
                "rplidar_c1_launch.py",
            )
        ),
        launch_arguments={"frame_id": "lidar_link"}.items(),
    )

    nav2_launch_file = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                autonomous_navigation_package,
                "launch",
                "navigation.launch.py",
            )
        ),
        launch_arguments={
            "params_file": configured_params,
            "autostart": "True",
        }.items(),
    )
    slam_toolbox_launch_file = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("slam_toolbox"),
                "launch",
                "online_async_launch.py",
            )
        ),
        launch_arguments={
            "slam_params_file": slam_toolbox_params,
        }.items(),
    )

    return LaunchDescription(
        [
            declare_use_rviz_cmd,
            #
            nav2_launch_file,
            #
            rviz_cmd,
            #
            drive_system,
            localization_system,
            slam_toolbox_launch_file,
            #
            imu_launch_file,
            lidar_launch_file,
            #
        ]
    )
