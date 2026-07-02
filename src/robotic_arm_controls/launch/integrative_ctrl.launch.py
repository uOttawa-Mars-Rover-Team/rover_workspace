import launch
import launch_ros.actions


def generate_launch_description():

    # ------------------------------------------------------------------
    # Controller 1
    # ------------------------------------------------------------------
    controller_1_joy = launch_ros.actions.Node(
        package="joy",
        executable="joy_node",
        name="joy_controller_1",
        parameters=[{"device_id": 0}],
        remappings=[("/joy", "/joy/controller_1")],
        output="screen",
    )

    # ------------------------------------------------------------------
    # Controller 2
    # ------------------------------------------------------------------
    controller_2_joy = launch_ros.actions.Node(
        package="joy",
        executable="joy_node",
        name="joy_controller_2",
        parameters=[{"device_id": 1}],
        remappings=[("/joy", "/joy/controller_2")],
        output="screen",
    )

    # ------------------------------------------------------------------
    # Integrative control node
    #   Hold LB → drive mode  (publishes Twist  on /cmd_vel_teleop)
    #   Hold RB → arm   mode  (publishes String on /arm_cmd)
    #
    # Arm string format:  S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!
    # Set dirXX to -1 to invert that joint's direction
    # ------------------------------------------------------------------
    integrative_control = launch_ros.actions.Node(
        package="robotic_arm_controls",
        executable="integrative_control",
        parameters=[
            {"scale_linear":  0.5},
            {"scale_angular": 0.5},
            {"dirTW": -1},
            {"dirL1":  1},
            {"dirL2": -1},
            {"dirWP":  1},
            {"dirWR":  1},
        ],
        output="screen",
    )

    # ------------------------------------------------------------------
    # Keyboard velocity override node
    # ------------------------------------------------------------------
    keyboard_controls = launch_ros.actions.Node(
        package="robotic_arm_controls",
        executable="ik_keyboard_controls",
        parameters=[{"mode": "M"}],
        output="screen",
    )

    # ------------------------------------------------------------------
    # Serial router — forwards /arm_cmd strings to microcontroller
    # ------------------------------------------------------------------
    m_router = launch_ros.actions.Node(
        package="robotic_arm_controls",
        executable="m_router",
        parameters=[
            {"timeout_delay": 0.1},
            {"serial_dev":    "/dev/ttyACM0"},
            {"baudrate":      9600},
            {"read_enable":   True},
        ],
        output="screen",
    )

    return launch.LaunchDescription([
        controller_1_joy,
        controller_2_joy,
        integrative_control,
        keyboard_controls,
        m_router,
    ])
