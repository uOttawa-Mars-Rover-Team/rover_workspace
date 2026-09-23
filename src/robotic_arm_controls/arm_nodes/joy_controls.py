#!/usr/bin/python3
"""Turn controller input into arm commands.

This is the node the arm actually runs on. It publishes a command string on
``/arm_cmd`` which ``m_router`` forwards over serial to the arm
microcontroller:

    S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!

The arm is flown with two controllers at once -- a flight stick for the tower
and the two links, an Xbox pad for the wrist and the peripherals. Which
controller a message came from is worked out from the message itself, not from
the device index ``joy_node`` happened to open it with, so they can be plugged
in in any order. See ``joy_cb``.

The ``mode`` parameter selects between that ("M", the default) and an
inverse-kinematics path ("I") that publishes ``TwistStamped`` on
``/servo_node/delta_twist_cmds`` and ``GripperControl`` on
``/gripper_control/gripper_velocities`` for MoveIt Servo. There is no IK stack
in this workspace at the moment -- the MoveIt config lives in an
``arm_controls`` package that is not in ``src/`` -- so "I" currently publishes
into the void. It is kept working so the arm side does not have to be
rewritten when IK comes back.
"""

from typing import TypeVar

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Float32, String

from general_interfaces.msg import ArmGpio, GripperControl

T = TypeVar("T")


# --- Joint slots, in the order they appear in the command string -----------
TW, L1, L2, WP, WR, SPARE = range(6)
JOINT_COUNT = 6


# --- Telling the controllers apart -----------------------------------------
# The number of buttons a controller reports is a property of the hardware, so
# unlike a device index it does not change when things are plugged in in a
# different order or enumerate differently on boot.
#
# To support a new controller: add its button count here, add its axis and
# button numbers below, and add a read_* method.
VELOCITYONE = "velocityone"   # Turtle Beach VelocityOne Flightstick
LOGITECH = "logitech"         # Logitech Extreme 3D Pro, the older stick
GAMEPAD = "gamepad"           # Xbox pad
SPACEMOUSE = "spacemouse"     # 3Dconnexion SpaceMouse, IK mode only

LAYOUT_BY_BUTTON_COUNT = {
    24: VELOCITYONE,
    12: LOGITECH,
    11: GAMEPAD,
    2: SPACEMOUSE,
}

# Input topics, each with the controller to assume when the button count is
# not one we recognise. The topic is only a fallback -- a recognised controller
# is read as itself whichever topic it turns up on. The arm_cmd_* names are
# what the launch files used before the stick and the pad had their own topics.
JOY_TOPICS = (
    ("/joy/arm_stick", VELOCITYONE),
    ("/joy/arm_pad", GAMEPAD),
    ("/joy/arm_cmd_logitech", VELOCITYONE),
    ("/joy/arm_cmd_xbox", GAMEPAD),
)


# --- Turtle Beach VelocityOne Flightstick (24 buttons) ---------------------
VO_AXIS_TW = 2                # stick twist        -> tower
VO_AXIS_L1 = 4                # stick fore/aft     -> link 1
VO_AXIS_L2 = 1                #                    -> link 2
VO_AXIS_DIAL = 5              # throttle           -> global speed
VO_BTN_VERBOSE = 2
VO_BTN_ENCODER_RESET = 3
VO_BTN_EE_OPEN = 15
VO_BTN_SERVO = 16
VO_BTN_EE_CLOSE = 17

# --- Logitech Extreme 3D Pro (12 buttons) ----------------------------------
LG_AXIS_TW = 2                # stick twist        -> tower
LG_AXIS_L1 = 1                # stick fore/aft     -> link 1
LG_AXIS_L2 = 5                # hat vertical       -> link 2
LG_AXIS_DIAL = 3              # throttle           -> global speed
LG_BTN_EE_CLOSE = 0           # IK mode only
LG_BTN_EE_OPEN = 1            # IK mode only
LG_BTN_TW_FASTER = 4
LG_BTN_TW_SLOWER = 5
LG_BTN_VERBOSE = 11

# --- Xbox pad (11 buttons) --------------------------------------------------
PAD_AXIS_CAM = 2              # left trigger -> shoulder camera servo down
PAD_BTN_CAM_UP = 4
PAD_BTN_STEPPER1 = 2          # TW
PAD_BTN_STEPPER2 = 3          # WP
PAD_BTN_STEPPER3 = 1          # WR
PAD_BTN_STEPPER4 = 0          # EE

# --- SpaceMouse (2 buttons), IK mode only ----------------------------------
SM_BTN_EE_CLOSE = 0
SM_BTN_EE_OPEN = 1


# Every joint at rest. Sent once at startup so the microcontroller is holding
# still rather than repeating whatever it was doing before this node came up.
STOP_CMD = "S;0.0;0.0;0.0;0.0;0.0;0.0;!"


def joint_field(value: float) -> str:
    """Format one joint of the command string.

    Adding 0.0 folds -0.0 into 0.0, so a joint that is not moving always
    serialises as "0.0" whether or not its direction is flipped -- otherwise a
    standing-still arm alternates between "0.0" and "-0.0" and every stop looks
    like a new command.
    """
    return str(round(value, 2) + 0.0)


class JoySource:
    """One physical controller, with every untouched input held at neutral.

    ``joy_node`` reports the state of every axis the moment it opens a device,
    and an axis nobody has touched yet does not necessarily read 0.0 -- a
    trigger or a throttle commonly sits at -1.0 or +1.0 until it is first
    moved. Feeding those values straight into a joint command is what made the
    arm take off the instant the launch file came up and only settle once the
    operator wiggled the sticks.

    So every axis starts out "not ready" and reads as 0.0; it only reports real
    values once it has been seen to move. Buttons work the same way: one that
    is already down in the very first message is ignored until it is released.
    """

    AXIS_EPS = 1e-3

    def __init__(self, name: str, logger):
        self.name = name
        self._logger = logger
        self._first_axes: list[float] = []
        self._axis_ready: list[bool] = []
        self._btn_ready: list[bool] = []
        self._axes: list[float] = []
        self._buttons: list[int] = []
        self._prev_buttons: list[int] = []
        self._seen = False

    def update(self, message: Joy) -> None:
        """Take in a new Joy message from this controller."""
        if (
            not self._seen
            or len(self._axis_ready) != len(message.axes)
            or len(self._btn_ready) != len(message.buttons)
        ):
            self._reset(message)

        for i, value in enumerate(message.axes):
            if not self._axis_ready[i] and abs(value - self._first_axes[i]) > self.AXIS_EPS:
                self._axis_ready[i] = True
        for i, value in enumerate(message.buttons):
            if not self._btn_ready[i] and not value:
                self._btn_ready[i] = True

        self._prev_buttons = self._buttons
        self._axes = list(message.axes)
        self._buttons = list(message.buttons)

    def axis(self, index: int) -> float:
        """Axis value, or 0.0 while that axis has not been moved yet."""
        if index >= len(self._axes) or not self._axis_ready[index]:
            return 0.0
        return self._axes[index]

    def button(self, index: int) -> int:
        """Button state, or 0 while that button has not been released yet."""
        if index >= len(self._buttons) or not self._btn_ready[index]:
            return 0
        return self._buttons[index]

    def prev_button(self, index: int) -> int:
        """Button state in the previous message from this controller."""
        if index >= len(self._prev_buttons):
            return 0
        return self._prev_buttons[index]

    def pressed(self, index: int) -> bool:
        """True on the message where the button goes down."""
        return bool(self.button(index)) and not self.prev_button(index)

    def released(self, index: int) -> bool:
        """True on the message where the button comes back up."""
        return not self.button(index) and bool(self.prev_button(index))

    def _reset(self, message: Joy) -> None:
        self._first_axes = list(message.axes)
        self._axis_ready = [False] * len(message.axes)
        self._btn_ready = [False] * len(message.buttons)
        self._axes = [0.0] * len(message.axes)
        self._buttons = [0] * len(message.buttons)
        self._prev_buttons = [0] * len(message.buttons)
        self._seen = True
        self._logger.info(
            f"{self.name} connected - each input stays neutral until it is moved"
        )


class JoyControls(Node):

    def __init__(self, node_name: str = "joy_controls"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # --- Parameters ----------------------------------------------------
        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.40)
        self.mode = self.get_param("mode", rclpy.Parameter.Type.STRING, "I")
        self.dirTW = self.get_param("dirTW", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL1 = self.get_param("dirL1", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL2 = self.get_param("dirL2", rclpy.Parameter.Type.INTEGER, 1)
        self.dirWP = self.get_param("dirWP", rclpy.Parameter.Type.INTEGER, 1)
        self.dirWR = self.get_param("dirWR", rclpy.Parameter.Type.INTEGER, 1)

        # The pad's two wrist axes are swapped between the two modes.
        if self.mode == "I":
            self.pad_axis_wp, self.pad_axis_wr = 0, 1
        else:
            self.pad_axis_wp, self.pad_axis_wr = 1, 0

        # --- Speed ----------------------------------------------------------
        # max_vel:    global scalar [0.4, 1.0], set by the throttle dial or by
        #             the keyboard node, applied to ALL joints.
        # max_vel_tw: tower-only scalar [0.1, 1.0], multiplied ON TOP of
        #             max_vel for the tower only.
        # Tower effective speed = max_vel * max_vel_tw
        self.max_vel = 1.0
        self.max_vel_tw = 1.0
        self.dial_raw = 0.0

        # --- Inputs ---------------------------------------------------------
        self.sources = {
            VELOCITYONE: JoySource("VelocityOne Flightstick", self.get_logger()),
            LOGITECH: JoySource("Logitech Extreme 3D Pro", self.get_logger()),
            GAMEPAD: JoySource("Xbox pad", self.get_logger()),
            SPACEMOUSE: JoySource("SpaceMouse", self.get_logger()),
        }
        self.readers = {
            VELOCITYONE: self.read_velocityone,
            LOGITECH: self.read_logitech,
            GAMEPAD: self.read_pad,
            SPACEMOUSE: lambda: None,
        }

        # Latest raw (un-deadbanded, un-scaled) value per joint slot. Each
        # controller writes only the slots it owns.
        self.raw_axes = [0.0] * JOINT_COUNT

        # --- Publishers ------------------------------------------------------
        self.cmd_pub = self.create_publisher(String, "/arm_cmd", 20)
        self.servo_pub = self.create_publisher(
            TwistStamped, "/servo_node/delta_twist_cmds", 20
        )
        self.vel_control_pub = self.create_publisher(
            GripperControl, "/gripper_control/gripper_velocities", 20
        )
        self.gpio_pub = self.create_publisher(
            ArmGpio, "/peripheral_controller/peripheral_enables", 10
        )

        self.arm_cmd = String()
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.header.frame_id = "base_footprint"
        self.vel_control_msg = GripperControl()
        self.gpio_cmd = ArmGpio()

        # --- Subscribers -----------------------------------------------------
        for topic, fallback in JOY_TOPICS:
            self.create_subscription(
                Joy, topic, self.make_joy_cb(topic, fallback), 20
            )

        self.create_subscription(Float32, "/keyboard/arm_vel", self.keyb_cb, 20)
        self.create_subscription(Float32, "/keyboard/arm_vel_tw", self.keyb_tw_cb, 20)

        # --- Outgoing command state -------------------------------------------
        self.prev_cmd = STOP_CMD
        self.servo_cmd_sent = False
        self.cam_down = False
        self.prev_cam_down = False
        self.prev_cam_up = 0
        self.identified: dict[str, str] = {}   # layout -> topic that claimed it

        # Hold the arm still on startup. Delayed so m_router has had time to
        # come up and subscribe, then cancelled -- this fires exactly once.
        if self.mode != "I":
            self.startup_timer = self.create_timer(1.0, self.send_startup_stop)

    # ------------------------------------------------------------------
    # Input routing
    # ------------------------------------------------------------------

    def make_joy_cb(self, topic: str, fallback: str):
        return lambda message: self.joy_cb(message, topic, fallback)

    def joy_cb(self, message: Joy, topic: str, fallback: str) -> None:
        """Route a Joy message to the controller it actually came from.

        The button count identifies the controller, which is what makes this
        immune to the two of them swapping device ids: a flight stick opened as
        device 1 instead of device 0 still drives the tower, and a pad that
        lands on the stick's topic is still read as a pad.

        A controller reporting a button count we have no layout for falls back
        to whatever that topic normally carries, so unfamiliar hardware still
        works as long as it is wired to the right topic.
        """
        layout = LAYOUT_BY_BUTTON_COUNT.get(len(message.buttons), fallback)
        self.note_identity(topic, layout, len(message.buttons))

        self.sources[layout].update(message)
        self.readers[layout]()
        self.publish_commands()

    def note_identity(self, topic: str, layout: str, buttons: int) -> None:
        """Log what each topic turned out to be carrying, once.

        Also catches the one case button counts cannot resolve: two different
        controllers that report the same number of buttons. They would both be
        read as the same device and fight over the same joints, so say so
        loudly rather than behaving strangely.
        """
        claimed = self.identified.get(layout)
        if claimed == topic:
            return
        if claimed is None:
            self.identified[layout] = topic
            known = buttons in LAYOUT_BY_BUTTON_COUNT
            self.get_logger().info(
                f"{topic}: {buttons} buttons -> {layout}"
                + ("" if known else " (unrecognised count, using the topic's default)")
            )
            return
        self.get_logger().error(
            f"{topic} and {claimed} both look like a {layout} ({buttons} buttons). "
            "They will fight over the same joints. Pin the controllers by name "
            "with the joy_a_name / joy_b_name launch arguments "
            "(ros2 run joy joy_enumerate_devices lists them)."
        )

    def read_velocityone(self) -> None:
        stick = self.sources[VELOCITYONE]
        self.raw_axes[TW] = stick.axis(VO_AXIS_TW)
        self.raw_axes[L1] = stick.axis(VO_AXIS_L1)
        self.raw_axes[L2] = stick.axis(VO_AXIS_L2)
        self.dial_raw = stick.axis(VO_AXIS_DIAL)

    def read_logitech(self) -> None:
        stick = self.sources[LOGITECH]
        self.raw_axes[TW] = stick.axis(LG_AXIS_TW)
        self.raw_axes[L1] = stick.axis(LG_AXIS_L1)
        self.raw_axes[L2] = stick.axis(LG_AXIS_L2)
        self.dial_raw = stick.axis(LG_AXIS_DIAL)

    def read_pad(self) -> None:
        pad = self.sources[GAMEPAD]
        self.raw_axes[WP] = pad.axis(self.pad_axis_wp)
        self.raw_axes[WR] = pad.axis(self.pad_axis_wr)
        # Trigger: released sits at +1.0, fully pressed at -1.0. JoySource
        # holds it at 0.0 until it is first moved, so an untouched trigger
        # cannot read as "held down" at startup.
        self.cam_down = pad.axis(PAD_AXIS_CAM) < 0

    # ------------------------------------------------------------------
    # Speed
    # ------------------------------------------------------------------

    def update_speed_from_dial(self) -> None:
        """Map the throttle dial onto the global speed scalar.

            raw -1.0  ->  max_vel 0.4  (slowest, at the motor stall floor)
            raw  0.0  ->  max_vel 0.7  (where an untouched dial sits)
            raw +1.0  ->  max_vel 1.0  (full speed)
        """
        new_speed = round(0.4 + 0.3 * (1.0 + self.dial_raw), 3)
        new_speed = max(0.4, min(1.0, new_speed))  # clamp to [0.4, 1.0]

        if abs(new_speed - self.max_vel) > 0.01:
            self.max_vel = new_speed
            self.get_logger().info(f"Max vel: {self.max_vel}")

    def update_tower_speed_buttons(self) -> None:
        """Logitech buttons 4/5 trim the tower-only speed scalar.

        Nothing equivalent is bound on the VelocityOne -- use the keyboard
        node's { and } keys there.
        """
        stick = self.sources[LOGITECH]
        if stick.pressed(LG_BTN_TW_FASTER):
            self.set_tower_scalar(round(self.max_vel_tw + 0.1, 1))
        elif stick.pressed(LG_BTN_TW_SLOWER):
            self.set_tower_scalar(round(self.max_vel_tw - 0.1, 1))

    def set_tower_scalar(self, value: float) -> None:
        if 0.1 <= value <= 1.0:
            self.max_vel_tw = value
            self.get_logger().info(
                f"Max tw scalar: {self.max_vel_tw}  ->  "
                f"tower speed: {round(self.max_vel * self.max_vel_tw, 3)}"
            )

    def scaled_axes(self) -> list[float]:
        """Snap each joint to 0 or +/- its speed, using the deadband.

        Every joint runs at ``max_vel``; the tower additionally gets the
        ``max_vel_tw`` trim, so its effective speed is max_vel * max_vel_tw.
        """
        scaled = []
        for slot, value in enumerate(self.raw_axes):
            speed = self.max_vel * self.max_vel_tw if slot == TW else self.max_vel
            if value > self.deadband:
                scaled.append(speed)
            elif value < -self.deadband:
                scaled.append(-speed)
            else:
                scaled.append(0.0)
        return scaled

    def keyb_cb(self, message: Float32) -> None:
        self.max_vel = round(message.data, 1)

    def keyb_tw_cb(self, message: Float32) -> None:
        self.max_vel_tw = round(message.data, 1)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------

    def publish_commands(self) -> None:
        self.update_speed_from_dial()
        if self.mode == "I":
            self.publish_ik()
        else:
            self.publish_manual()

    def publish_ik(self) -> None:
        """IK mode: hand the axes to MoveIt Servo as a twist."""
        axes = self.scaled_axes()

        self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()
        self.twist_stamped_msg.twist.linear.x = axes[TW]
        self.twist_stamped_msg.twist.linear.y = axes[L1]
        self.twist_stamped_msg.twist.linear.z = axes[L2]
        self.vel_control_msg.roll_velocity = axes[WP]
        self.twist_stamped_msg.twist.angular.y = axes[WR]
        self.twist_stamped_msg.twist.angular.z = axes[SPARE]

        self.vel_control_msg.ee_velocity = 0.0
        for layout, close_btn, open_btn in (
            (SPACEMOUSE, SM_BTN_EE_CLOSE, SM_BTN_EE_OPEN),
            (LOGITECH, LG_BTN_EE_CLOSE, LG_BTN_EE_OPEN),
        ):
            source = self.sources[layout]
            if source.button(close_btn) or source.button(open_btn):
                self.vel_control_msg.ee_velocity = self.max_vel
                break

        self.servo_pub.publish(self.twist_stamped_msg)
        self.vel_control_pub.publish(self.vel_control_msg)

    def publish_manual(self) -> None:
        """Manual mode: build and send the S;...;! joint command string."""
        self.update_tower_speed_buttons()
        self.handle_verbose_button()
        self.handle_camera_servo()
        self.handle_stepper_toggles()
        self.handle_stick_buttons()

        stick = self.sources[VELOCITYONE]
        axes = self.scaled_axes()
        cmd = "S;"
        cmd += joint_field(axes[TW] * self.dirTW) + ";"
        cmd += joint_field(axes[L1] * self.dirL1) + ";"
        cmd += joint_field(axes[L2] * self.dirL2) + ";"
        cmd += joint_field(axes[WP] * self.dirWP) + ";"
        cmd += joint_field(axes[WR] * self.dirWR) + ";"

        if stick.button(VO_BTN_EE_CLOSE):
            cmd += joint_field(-self.max_vel)
        elif stick.button(VO_BTN_EE_OPEN):
            cmd += joint_field(self.max_vel)
        else:
            cmd += "0.0"
        cmd += ";!"

        if cmd != self.prev_cmd:
            self.prev_cmd = cmd
            self.command_pub(cmd)

    def send_startup_stop(self) -> None:
        """One-shot: tell the arm to hold still before anyone touches a stick."""
        self.startup_timer.cancel()
        self.command_pub(STOP_CMD)

    # ------------------------------------------------------------------
    # Manual-mode buttons
    # ------------------------------------------------------------------

    def handle_verbose_button(self) -> None:
        if self.sources[LOGITECH].pressed(LG_BTN_VERBOSE):
            self.toggle_verbose()

    def handle_camera_servo(self) -> None:
        """Pad button 4 raises the shoulder camera, the trigger lowers it."""
        cam_up = self.sources[GAMEPAD].button(PAD_BTN_CAM_UP)

        if cam_up:
            self.send_servo_command("SV;C;1", "Shoulder camera servo: up")
        elif self.cam_down:
            self.send_servo_command("SV;C;-1", "Shoulder camera servo: down")
        elif self.prev_cam_down or self.prev_cam_up:
            self.servo_cmd_sent = False
            self.send_command("SV;C;0", "Stop shoulder camera servo")

        self.prev_cam_down = self.cam_down
        self.prev_cam_up = cam_up

    def handle_stepper_toggles(self) -> None:
        """Pad face buttons enable/disable each stepper driver."""
        pad = self.sources[GAMEPAD]
        if pad.pressed(PAD_BTN_STEPPER1):
            self.toggle_gpio("stepper1_en", "TW", "RA;stepper1")
        if pad.pressed(PAD_BTN_STEPPER2):
            self.toggle_gpio("stepper2_en", "WP", "RA;stepper2")
        if pad.pressed(PAD_BTN_STEPPER3):
            self.toggle_gpio("stepper3_en", "WR", "RA;stepper3")
        if pad.pressed(PAD_BTN_STEPPER4):
            self.toggle_gpio("stepper4_en", "EE", "RA;stepper4")

    def handle_stick_buttons(self) -> None:
        """VelocityOne buttons that are not joints or the gripper."""
        stick = self.sources[VELOCITYONE]

        # Servo button: tap -> svT, held -> svH (repeats), release -> svR
        if stick.pressed(VO_BTN_SERVO):
            self.send_raw_command("RA;svT!", "RA button: tap")
        elif stick.button(VO_BTN_SERVO) and stick.prev_button(VO_BTN_SERVO):
            self.send_raw_command("RA;svH!", "RA button: held")
        elif stick.released(VO_BTN_SERVO):
            self.send_raw_command("RA;svR!", "RA button: released")

        if stick.pressed(VO_BTN_VERBOSE):
            self.send_raw_command("RA;VBS!", "Verbosity Toggled")
        if stick.pressed(VO_BTN_ENCODER_RESET):
            self.send_raw_command("RA;SET0!", "All encoders reset")

    def toggle_gpio(self, attr: str, label: str, cmd_str: str) -> None:
        current = getattr(self.gpio_cmd, attr)
        setattr(self.gpio_cmd, attr, not current)

        self.get_logger().info(f"{label} toggled: {not current}")
        if self.mode == "M":
            self.send_raw_command(f"{cmd_str}!", f"{label} stepper toggled")
        else:
            self.gpio_pub.publish(self.gpio_cmd)

    def toggle_verbose(self) -> None:
        self.get_logger().info("Verbose toggled")
        if self.mode == "M":
            self.command_pub("v;!")

    # ------------------------------------------------------------------
    # /arm_cmd helpers
    # ------------------------------------------------------------------

    def send_servo_command(self, data: str, label: str) -> None:
        """Send once per press, not once per Joy message."""
        if not self.servo_cmd_sent:
            self.send_command(data, label)
            self.servo_cmd_sent = True

    def send_command(self, data: str, label: str) -> None:
        """Publish ``data`` with the ';!' terminator appended."""
        self.get_logger().info(label)
        self.command_pub(f"{data};!")

    def send_raw_command(self, data: str, label: str) -> None:
        """Publish ``data`` exactly as given, for commands that already carry
        their own terminator (e.g. 'RA;svT!')."""
        self.get_logger().info(label)
        self.command_pub(data)

    def command_pub(self, data: str) -> None:
        self.arm_cmd.data = data
        self.get_logger().info("Command sent: " + data)
        self.cmd_pub.publish(self.arm_cmd)

    # ------------------------------------------------------------------
    # Parameter helper
    # ------------------------------------------------------------------

    def get_param(
        self,
        param_name: str,
        param_type: rclpy.Parameter.Type,
        default_val: T | None = None,
        logging: bool = True,
    ) -> T:
        self.declare_parameter(param_name, param_type)
        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = Parameter(param_name, param_type, default_val)
            param_val = self.get_parameter_or(param_name, default_param).value
        assert param_val is not None, "The parameter received was None."
        if logging:
            self.get_logger().info(f"Using {param_name}: {param_val}")
        return param_val


def main(args=None):
    rclpy.init(args=args)
    controller = JoyControls()
    rclpy.spin(controller)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
