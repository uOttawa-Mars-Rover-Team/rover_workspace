"""Arm software that runs ON THE ROVER while the operator drives from the base
station.

    ros2 launch robotic_arm_controls rover_arm.launch.py

Pair this with basestation_arm.launch.py on the operator laptop. All joystick
handling happens base-station side; the rover's only job is to push the
/arm_cmd strings down the serial link to the arm microcontroller.

If you are sitting at the rover with the controllers plugged straight into it,
use manual.launch.py instead -- that runs both halves on one machine.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    serial_dev = DeclareLaunchArgument(
        "serial_dev",
        default_value="/dev/ttyACM0",
        description="Serial port the arm microcontroller is plugged into.",
    )

    # Forwards every /arm_cmd string over serial to the arm microcontroller.
    # baudrate must match the firmware in rover_embedded_shield.
    router = Node(
        package="robotic_arm_controls",
        executable="m_router",
        parameters=[
            {
                "timeout_delay": 0.1,
                "serial_dev": LaunchConfiguration("serial_dev"),
                "baudrate": 9600,
                "read_enable": True,
            }
        ],
        output="screen",
    )

    return LaunchDescription([serial_dev, router])
