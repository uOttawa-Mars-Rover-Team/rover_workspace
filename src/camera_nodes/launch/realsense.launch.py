import os
import launch
import launch_ros.actions
from launch.substitutions import Command
from launch.actions import IncludeLaunchDescription
from ament_index_python import get_package_share_directory
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_path
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    robot_description = ParameterValue(
        Command(
            [
                "xacro ",
                str(
                    get_package_share_path("realsense2_description")
                    / "urdf/test_d435_camera.urdf.xacro"
                ),
            ]
        ),
        value_type=str,
    )

    rs_cam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("realsense2_camera"), "launch/rs_launch.py"
            )
        ),
        launch_arguments={
            "depth_module.profile": "640x480x30",
            # "pointcloud.enable": "True",
        }.items(),
    )

    return launch.LaunchDescription(
        [
            rs_cam,
            launch_ros.actions.Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
        ]
    )
