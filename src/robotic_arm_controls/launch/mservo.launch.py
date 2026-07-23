import launch
import launch_ros

from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


# Router-only bring-up for the mservo terminal GUI + Arm_V2_2 firmware.
#
# Deliberately isolated from *_manual.launch.py:
#   - No ik_joy_controls / ik_keyboard_controls (they publish their own frames on
#     the SAME /arm_cmd topic and would fight the GUI's S;... commands).
#   - Baud fixed at 9600 to match Arm_V2_2_Controls_SPI.
#   - read_enable=False: m_router's serial read thread currently crashes logging
#     raw bytes (arm f;/g; feedback), so keep it off until that legacy bug is fixed.
#
# Run the GUI separately in its own terminal (it does a full-screen redraw and
# grabs the keyboard, so it must NOT share stdout with launched nodes):
#     ros2 run robotic_arm_controls mservo_gui_term
def generate_launch_description():
    serial_dev = LaunchConfiguration("serial_dev")

    m_router = launch_ros.actions.Node(
        package="robotic_arm_controls",
        executable="m_router",
        name="m_router",
        parameters=[
            {
                "timeout_delay": 0.1,
                "serial_dev": serial_dev,
                "baudrate": 9600,     # Arm_V2_2 BAUDRATE
                "read_enable": False,  # read thread bug: keep off for now
            }
        ],
        output="screen",
    )

    return launch.LaunchDescription(
        [
            DeclareLaunchArgument(
                "serial_dev",
                default_value="/dev/arm_mega",
                description="Serial port of the arm Mega (override per machine).",
            ),
            m_router,
        ]
    )
