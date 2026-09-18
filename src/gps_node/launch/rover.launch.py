import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    ublox_dgnss_pkg = get_package_share_directory("ublox_dgnss")
    start_joystick_control_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ublox_dgnss_pkg,
                "launch",
                "ublox_fb+r_rover.launch.py",
            )
        ),
    )

    return LaunchDescription(
        [
            start_joystick_control_cmd,
        ]
    )
