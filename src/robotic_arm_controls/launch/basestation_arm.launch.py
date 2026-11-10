"""Arm control from the operator laptop at the base station.

    ros2 launch robotic_arm_controls basestation_arm.launch.py

Reads the controllers, turns them into /arm_cmd strings and puts those on the
network. Run rover_arm.launch.py on the rover at the same time -- that is what
picks /arm_cmd up and pushes it over serial to the arm.

Controllers
-----------
A VelocityOne Flightstick for the tower and links, an Xbox pad for the wrist
and the peripherals. It does NOT matter which joy node picks up which:
joy_controls identifies each controller from the Joy message it sends, not
from the device index. Plug them in in any order.

If a device index picks up the wrong thing entirely, pin them by name:

    ros2 run joy joy_enumerate_devices          # lists index + exact name
    ros2 launch robotic_arm_controls basestation_arm.launch.py \\
        joy_a_name:="VelocityOne Flightstick"

A name, when given, takes priority over the index.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


# --- Set once, when the arm is built or rewired ----------------------------

# Per-joint direction. Flip one to -1 if that joint drives the wrong way.
JOINT_DIRECTIONS = {
    "dirTW": -1,
    "dirL1": -1,
    "dirL2": 1,
    "dirWP": 1,
    "dirWR": 1,
}

# How far a stick has to leave centre before it counts as a command, 0.0 - 1.0.
DEADBAND = 0.4


def joy_node(node_name: str, id_arg: str, name_arg: str, topic: str) -> Node:
    """One joy_node reading one controller."""
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
        output="screen",
    )


def generate_launch_description():
    arguments = [
        DeclareLaunchArgument(
            "mode",
            default_value="M",
            description=(
                '"M" for manual joint control. "I" switches to the IK path, '
                "which has nothing listening to it until the MoveIt config "
                "comes back into the workspace."
            ),
        ),
        DeclareLaunchArgument(
            "joy_a_id", default_value="0", description="Device index of the flight stick."
        ),
        DeclareLaunchArgument(
            "joy_b_id", default_value="1", description="Device index of the pad."
        ),
        DeclareLaunchArgument(
            "joy_a_name",
            default_value="",
            description="Exact device name of the flight stick; overrides joy_a_id.",
        ),
        DeclareLaunchArgument(
            "joy_b_name",
            default_value="",
            description="Exact device name of the pad; overrides joy_b_id.",
        ),
    ]

    mode = LaunchConfiguration("mode")

    controllers = [
        joy_node("joy_stick", "joy_a_id", "joy_a_name", "/joy/arm_stick"),
        joy_node("joy_pad", "joy_b_id", "joy_b_name", "/joy/arm_pad"),
    ]

    # Keyboard: speed trim and a few toggles. See the README for the key map.
    keyboard = Node(
        package="robotic_arm_controls",
        executable="keyboard_controls",
        parameters=[{"mode": mode}],
        output="screen",
    )

    # The controller -> arm command node.
    arm_controls = Node(
        package="robotic_arm_controls",
        executable="joy_controls",
        parameters=[{"mode": mode, "deadband": DEADBAND}, JOINT_DIRECTIONS],
        output="screen",
    )

    return LaunchDescription(arguments + controllers + [keyboard, arm_controls])
