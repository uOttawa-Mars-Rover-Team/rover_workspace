"""Drive and arm from Xbox pads, on one machine.

    ros2 launch robotic_arm_controls integrative.launch.py              # two pads
    ros2 launch robotic_arm_controls integrative.launch.py controllers:=1

One pad does both jobs, held down like a shift key:

    hold LB  ->  drive     publishes Twist  on /cmd_vel_teleop
    hold RB  ->  arm       publishes String on /arm_cmd
    neither, or both       nothing is published (safe stop)

With two pads, each is handled independently with its own state, so two
operators can work at once -- one driving, one on the arm.

This is the drive-capable alternative to manual.launch.py, which is arm only
and uses the flight stick. Run one or the other, never both: they both start a
serial router and both publish to /arm_cmd.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import EqualsSubstitution, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


# --- Set once, when the arm is built or rewired ----------------------------

# Per-joint direction. Flip one to -1 if that joint drives the wrong way.
JOINT_DIRECTIONS = {
    "dirTW": -1,
    "dirL1": 1,
    "dirL2": -1,
    "dirWP": 1,
    "dirWR": 1,
}

# Drive speed. Holding Y multiplies both by turbo_mult.
DRIVE_SCALING = {
    "scale_linear": 0.5,
    "scale_angular": 0.5,
    "turbo_mult": 2.0,
    "dirTurn": 1,
}

# Topics the pads publish on. integrative_control keeps separate state per
# topic, which is what lets two operators work at the same time.
PAD_1_TOPIC = "/joy/controller_1"
PAD_2_TOPIC = "/joy/controller_2"


def joy_node(node_name: str, id_arg: str, name_arg: str, topic: str, condition=None) -> Node:
    """One joy_node reading one pad."""
    return Node(
        package="joy",
        executable="joy_node",
        name=node_name,
        parameters=[
            {
                "device_id": ParameterValue(LaunchConfiguration(id_arg), value_type=int),
                "device_name": ParameterValue(
                    LaunchConfiguration(name_arg), value_type=str
                ),
            }
        ],
        remappings=[("/joy", topic)],
        condition=condition,
        output="screen",
    )


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument(
            "controllers",
            default_value="2",
            choices=["1", "2"],
            description="How many Xbox pads are plugged in.",
        ),
        DeclareLaunchArgument(
            "serial_dev",
            default_value="/dev/ttyACM0",
            description="Serial port the arm microcontroller is plugged into.",
        ),
        DeclareLaunchArgument(
            "joy_a_id", default_value="0", description="Device index of the first pad."
        ),
        DeclareLaunchArgument(
            "joy_b_id", default_value="1", description="Device index of the second pad."
        ),
        DeclareLaunchArgument(
            "joy_a_name",
            default_value="",
            description="Exact device name of the first pad; overrides joy_a_id.",
        ),
        DeclareLaunchArgument(
            "joy_b_name",
            default_value="",
            description="Exact device name of the second pad; overrides joy_b_id.",
        ),
    ]

    controllers = [
        joy_node("joy_pad_1", "joy_a_id", "joy_a_name", PAD_1_TOPIC),
        # Only started when controllers:=2, otherwise joy_node would sit there
        # failing to open a device that is not plugged in.
        joy_node(
            "joy_pad_2",
            "joy_b_id",
            "joy_b_name",
            PAD_2_TOPIC,
            condition=IfCondition(
                EqualsSubstitution(LaunchConfiguration("controllers"), "2")
            ),
        ),
    ]

    # Keyboard: arm speed trim. integrative_control picks the values up on
    # /keyboard/arm_vel and /keyboard/arm_vel_tw.
    keyboard = Node(
        package="robotic_arm_controls",
        executable="keyboard_controls",
        parameters=[{"mode": "M"}],
        output="screen",
    )

    # The combined drive + arm node.
    integrative_controls = Node(
        package="robotic_arm_controls",
        executable="integrative_control",
        parameters=[DRIVE_SCALING, JOINT_DIRECTIONS],
        output="screen",
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

    return LaunchDescription(
        arguments + controllers + [keyboard, integrative_controls, router]
    )
