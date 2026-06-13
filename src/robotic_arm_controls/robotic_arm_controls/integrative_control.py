#!/usr/bin/python3

from typing import TypeVar
from concurrent.futures import ThreadPoolExecutor

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String, Float32
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Xbox One button/axis indices  (ROS joy_node, xpad/xboxdrv driver)
# ---------------------------------------------------------------------------
#
#  AXES:
#   0  = Left  stick X   left=+1  right=-1
#   1  = Left  stick Y   up=+1    down=-1
#   2  = Left  trigger   released=+1  full=-1   (unused)
#   3  = Right stick X   left=+1  right=-1
#   4  = Right stick Y   up=+1    down=-1
#   5  = Right trigger   released=+1  full=-1   (unused)
#   6  = D-pad X         left=+1  right=-1      (unused)
#   7  = D-pad Y         up=+1    down=-1
#
#  BUTTONS:
#   0  = A
#   1  = B
#   2  = X
#   3  = Y    ← hold for TURBO mode
#   4  = LB   ← hold for DRIVE mode
#   5  = RB   ← hold for ARM   mode
#   6  = Back / View
#   7  = Start / Menu
#   8  = Xbox / Guide
#   9  = Left  stick click
#   10 = Right stick click
# ---------------------------------------------------------------------------

BTN_A  = 0
BTN_B  = 1
BTN_Y  = 3
BTN_LB = 4
BTN_RB = 5

AXIS_LS_X   = 0   # WR  wrist roll
AXIS_LS_Y   = 1   # WP  wrist pitch
AXIS_RS_X   = 3   # TW  tower / base twist
AXIS_RS_Y   = 4   # L1  link 1
AXIS_DPAD_Y = 7   # L2  link 2

NUM_AXES = 8
NUM_BTNS = 11

# Right stick deadband is intentionally high to prevent accidental
# simultaneous TW + L1 commands from stick drift
DEADBAND_LS   = 0.15
DEADBAND_RS   = 0.50
DEADBAND_DPAD = 0.50


class IntegrativeControl(Node):
    """
    Dual-mode Xbox One controller node.

    Hold LB  →  DRIVE mode
                  Publishes geometry_msgs/Twist on /cmd_vel_teleop
                  Left stick Y = linear.x   (forward / back)
                  Left stick X = angular.z  (turn)
                  Hold Y       = Turbo multiplier applied

    Hold RB  →  ARM mode
                  Publishes std_msgs/String on /arm_cmd
                  Format:  S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!

                  Right stick X → TW  (tower / base twist)   [high deadband]
                  Right stick Y → L1                          [high deadband]
                  D-pad Y       → L2
                  Left  stick Y → WP  (wrist pitch)
                  Left  stick X → WR  (wrist roll)
                  A held        → EE close  (-max_vel)
                  B held        → EE open   (+max_vel)

    Neither or both bumpers held → nothing published (safe stop).

    Two controllers on /joy/controller_1 and /joy/controller_2 are handled
    independently with fully isolated state.
    """

    def __init__(self, node_name: str = "integrative_control"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node: {self.get_fully_qualified_name()}")

        # ---- parameters (overridable from launch file) ----------------
        self.scale_linear  = self.get_param("scale_linear",  Parameter.Type.DOUBLE, 0.5)
        self.scale_angular = self.get_param("scale_angular", Parameter.Type.DOUBLE, 0.5)
        self.turbo_mult    = self.get_param("turbo_mult",    Parameter.Type.DOUBLE, 2.0)

        # Deadbands - tunable for different controller sensitivities
        self.deadband_ls = self.get_param("deadband_ls", Parameter.Type.DOUBLE, DEADBAND_LS)
        self.deadband_rs = self.get_param("deadband_rs", Parameter.Type.DOUBLE, DEADBAND_RS)
        self.deadband_dp = self.get_param("deadband_dp", Parameter.Type.DOUBLE, DEADBAND_DPAD)

        # Direction flips — set to -1 in launch file to invert a joint
        self.dirTurn = self.get_param("dirTurn", Parameter.Type.INTEGER, 1) # 1 = Left is positive Z
        self.dirTW = self.get_param("dirTW", Parameter.Type.INTEGER, 1)
        self.dirL1 = self.get_param("dirL1", Parameter.Type.INTEGER, 1)
        self.dirL2 = self.get_param("dirL2", Parameter.Type.INTEGER, 1)
        self.dirWP = self.get_param("dirWP", Parameter.Type.INTEGER, 1)
        self.dirWR = self.get_param("dirWR", Parameter.Type.INTEGER, 1)

        # Arm velocity scales — overridable at runtime via keyboard node
        self.max_vel    = 1.0
        self.max_vel_tw = 1.0

        # ---- publishers -----------------------------------------------
        self.drive_pub = self.create_publisher(Twist,  "/cmd_vel_teleop", 10)
        self.cmd_pub   = self.create_publisher(String, "/arm_cmd",        10)

        # ---- subscribers ----------------------------------------------
        self._init_controller_state("ctrl1")
        self._init_controller_state("ctrl2")

        self.create_subscription(
            Joy, "/joy/controller_1",
            lambda msg: self._joy_cb(msg, "ctrl1"), 20
        )
        self.create_subscription(
            Joy, "/joy/controller_2",
            lambda msg: self._joy_cb(msg, "ctrl2"), 20
        )

        self.create_subscription(Float32, "/keyboard/arm_vel",    self._keyb_cb,    20)
        self.create_subscription(Float32, "/keyboard/arm_vel_tw", self._keyb_tw_cb, 20)

        self.tp = ThreadPoolExecutor(max_workers=4)
        self._prev_arm_cmd = {"ctrl1": "", "ctrl2": ""}

    # ------------------------------------------------------------------
    # Per-controller state helpers
    # ------------------------------------------------------------------

    def _init_controller_state(self, cid: str):
        self.__dict__[f"{cid}_axes"]      = [0.0] * NUM_AXES
        self.__dict__[f"{cid}_btns"]      = [0]   * NUM_BTNS
        self.__dict__[f"{cid}_prev_btns"] = [0]   * NUM_BTNS

    def _state(self, cid: str):
        return (
            self.__dict__[f"{cid}_axes"],
            self.__dict__[f"{cid}_btns"],
            self.__dict__[f"{cid}_prev_btns"],
        )

    # ------------------------------------------------------------------
    # Top-level Joy callback
    # ------------------------------------------------------------------

    def _joy_cb(self, msg: Joy, cid: str):
        if len(msg.axes) < NUM_AXES or len(msg.buttons) < NUM_BTNS:
            self.get_logger().warn(
                f"[{cid}] Unexpected Joy message size "
                f"(axes={len(msg.axes)}, btns={len(msg.buttons)}). "
                "Is this an Xbox One controller?"
            )
            return

        axes, btns, prev_btns = self._state(cid)

        for i in range(NUM_AXES):
            axes[i] = msg.axes[i]
        for i in range(NUM_BTNS):
            btns[i] = msg.buttons[i]

        lb_held = bool(btns[BTN_LB])
        rb_held = bool(btns[BTN_RB])

        if lb_held and not rb_held:
            self._drive_handler(axes, btns)
        elif rb_held and not lb_held:
            self._arm_handler(axes, btns, cid)
        # both or neither → publish nothing (safe stop)

        self.__dict__[f"{cid}_prev_btns"] = list(btns)

    # ------------------------------------------------------------------
    # DRIVE MODE  (LB held)
    # ------------------------------------------------------------------

    def _drive_handler(self, axes, btns):
        raw_linear  = axes[AXIS_LS_Y]
        raw_angular = axes[AXIS_LS_X]

        if abs(raw_linear)  < self.deadband_ls: raw_linear  = 0.0
        if abs(raw_angular) < self.deadband_ls: raw_angular = 0.0

        multiplier = self.turbo_mult if btns[BTN_Y] else 1.0

        twist = Twist()
        twist.linear.x  = raw_linear  * self.scale_linear * multiplier
        twist.angular.z = raw_angular * self.scale_angular * multiplier * self.dirTurn

        self.tp.submit(self.drive_pub.publish, twist)

    # ------------------------------------------------------------------
    # ARM MODE  (RB held)
    #
    # Output string format:  S;<TW>;<L1>;<L2>;<WP>;<WR>;<EE>;!
    # ------------------------------------------------------------------

    def _arm_handler(self, axes, btns, cid: str):

        tw = self._snap(axes[AXIS_RS_X],   self.deadband_rs) * self.max_vel_tw * self.dirTW
        l1 = self._snap(axes[AXIS_RS_Y],   self.deadband_rs) * self.max_vel    * self.dirL1
        l2 = self._snap(axes[AXIS_DPAD_Y], self.deadband_dp) * self.max_vel    * self.dirL2
        wp = self._snap(axes[AXIS_LS_Y],   self.deadband_ls) * self.max_vel    * self.dirWP
        wr = self._snap(axes[AXIS_LS_X],   self.deadband_ls) * self.max_vel    * self.dirWR

        if btns[BTN_A]:
            ee = -self.max_vel   # close
        elif btns[BTN_B]:
            ee =  self.max_vel   # open
        else:
            ee = 0.0

        cmd = (
            f"S;"
            f"{round(tw, 2)};"
            f"{round(l1, 2)};"
            f"{round(l2, 2)};"
            f"{round(wp, 2)};"
            f"{round(wr, 2)};"
            f"{round(ee, 2)};!"
        )

        if cmd != self._prev_arm_cmd[cid]:
            self._prev_arm_cmd[cid] = cmd
            msg = String()
            msg.data = cmd
            self.get_logger().info(f"[{cid}] {cmd}")
            self.tp.submit(self.cmd_pub.publish, msg)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _snap(self, value: float, deadband: float) -> float:
        """Snap to +1 / -1 / 0 based on deadband threshold."""
        if value >  deadband: return  1.0
        if value < -deadband: return -1.0
        return 0.0

    def _keyb_cb(self, msg: Float32):
        self.max_vel = round(msg.data, 1)

    def _keyb_tw_cb(self, msg: Float32):
        self.max_vel_tw = round(msg.data, 1)

    def get_param(self, name, ptype, default=None):
        self.declare_parameter(name, ptype)
        if default is None:
            return self.get_parameter(name).value
        return self.get_parameter_or(name, Parameter(name, ptype, default)).value


# ---------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = IntegrativeControl()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()