#!/usr/bin/env python3
"""
GameSir Nova Lite Rover Teleop + Arm Servo Control + Live Monitor

Run joy_node separately first:
    ros2 run joy joy_node --ros-args -p device_id:=0 -p deadzone:=0.05 -p autorepeat_rate:=20.0

Then run this script:
    python3 rover_teleop.py

Drive:   LB (enable) + RT/LT = forward/back, Left Stick X = turn
Speed:   A + D-pad Up/Down = speed adjust
Turn:    X + D-pad Left/Right = turn adjust
Arm A:   D-pad axes -> /arm_cmd  (sends "SV;A;x;y!" only on change)
Arm B:   Right stick  -> /arm_cmd  (sends "SV;B;x;y!" only on change)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import os
import sys
import time
import subprocess
import threading

W = 48

BTN_NAMES = [
    "A", "B", "X", "Y",
    "LB", "RB", "Back", "Start",
    "Home", "LClick", "RClick",
    "B11", "B12", "B13", "B14", "B15",
]


class TUI:
    """Flicker-free terminal drawing — builds a single string, writes once."""

    def __init__(self):
        self.lines = []
        self.prev_line_count = 0

    def row(self, text):
        self.lines.append(f"║ {text:<{W}} ║")

    def hline(self, left, right, fill="═"):
        self.lines.append(left + fill * (W + 2) + right)

    def blank(self):
        self.row("")

    def flush(self):
        while len(self.lines) < self.prev_line_count:
            self.lines.append(" " * (W + 4))
        self.prev_line_count = len(self.lines)
        buf = "\033[H" + "\n".join(self.lines) + "\n"
        sys.stdout.write(buf)
        sys.stdout.flush()
        self.lines = []


def tbar(pct, w=20):
    f = int(pct / 100.0 * w)
    return f"[{'#' * f}{'.' * (w - f)}] {pct:>5.1f}%"


def sbar(pct, w=20):
    c = w // 2
    f = int(abs(pct) / 100.0 * c)
    if pct > 0:
        return f"[{'.' * c}|{'#' * f}{'.' * (c - f)}] {pct:>+6.1f}%"
    elif pct < 0:
        return f"[{'.' * (c - f)}{'#' * f}|{'.' * c}] {pct:>+6.1f}%"
    return f"[{'.' * c}|{'.' * c}] {pct:>+6.1f}%"


class CombinedTeleop(Node):
    def __init__(self):
        super().__init__("combined_teleop")

        self.enable_btn   = int(os.environ.get("ENABLE_BUTTON", "4"))
        self.spd_btn      = int(os.environ.get("SPEED_BUTTON",  "0"))
        self.turn_btn     = int(os.environ.get("TURN_BUTTON",   "2"))

        self.dpad_up      = int(os.environ.get("DPAD_UP",    "12"))
        self.dpad_down    = int(os.environ.get("DPAD_DOWN",  "13"))
        self.dpad_left    = int(os.environ.get("DPAD_LEFT",  "14"))
        self.dpad_right   = int(os.environ.get("DPAD_RIGHT", "15"))

        self.axis_lx      = int(os.environ.get("AXIS_LX",      "0"))
        self.axis_lt      = int(os.environ.get("AXIS_LT",      "2"))
        self.axis_rt      = int(os.environ.get("AXIS_RT",      "5"))
        self.axis_dpad_lr = int(os.environ.get("AXIS_DPAD_LR", "6"))
        self.axis_dpad_ud = int(os.environ.get("AXIS_DPAD_UD", "7"))

        # Right stick axes
        self.axis_rx      = int(os.environ.get("AXIS_RX", "3"))
        self.axis_ry      = int(os.environ.get("AXIS_RY", "4"))

        self.speed    = float(os.environ.get("DEFAULT_SPEED", "0.7"))
        self.turn     = float(os.environ.get("DEFAULT_TURN",  "0.4"))
        self.max_spd  = float(os.environ.get("MAX_SPEED",     "2.0"))
        self.min_spd  = float(os.environ.get("MIN_SPEED",     "0.1"))
        self.max_trn  = float(os.environ.get("MAX_TURN",      "1.5"))
        self.min_trn  = float(os.environ.get("MIN_TURN",      "0.1"))
        self.spd_step = float(os.environ.get("SPEED_STEP",    "0.1"))
        self.trn_step = float(os.environ.get("TURN_STEP",     "0.05"))

        # Right stick deadzone
        self.rstick_deadzone = float(os.environ.get("RSTICK_DEADZONE", "0.3"))

        drive_topic    = os.environ.get("OUTPUT_TOPIC",  "cmd_vel_teleop")
        arm_topic      = os.environ.get("ARM_CMD_TOPIC", "/arm_cmd")
        self.jetson_ip = os.environ.get("JETSON_IP",     "192.168.1.201")

        self.invert_x = os.environ.get("ARM_INVERT_X", "false").lower() == "true"
        self.invert_y = os.environ.get("ARM_INVERT_Y", "false").lower() == "true"

        self.axes             = []
        self.buttons          = []
        self.prev_buttons     = []
        self.cmd              = Twist()
        self.last_action      = ""
        self.last_action_time = 0
        self.started          = False

        self.dpad_is_axes   = True
        self.prev_dpad_axis = [0.0, 0.0]
        self.last_arm_a_cmd = None
        self.last_arm_b_cmd = None

        self.jetson_reachable    = False
        self.ping_thread_running = True
        threading.Thread(target=self._ping_loop, daemon=True).start()

        self.drive_pub = self.create_publisher(Twist,  f"/{drive_topic}", 10)
        self.arm_pub   = self.create_publisher(String, arm_topic,         20)
        self.create_subscription(Joy, "/joy", self.on_joy, 10)

        self.tui = TUI()
        self.create_timer(1.0 / 15.0, self.draw)

        sys.stdout.write("\033[?25l\033[2J")
        sys.stdout.flush()

        self.get_logger().info("Combined teleop node started")

    def _ping_loop(self):
        while self.ping_thread_running:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "1", self.jetson_ip],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=3,
                )
                self.jetson_reachable = (result.returncode == 0)
            except Exception:
                self.jetson_reachable = False
            time.sleep(5.0)

    def btn(self, i):
        return self.buttons[i] if i < len(self.buttons) else 0

    def axis(self, i):
        return self.axes[i] if i < len(self.axes) else 0.0

    def trig_pct(self, i):
        if i >= len(self.axes):
            return 0.0
        pct = (1.0 - self.axes[i]) / 2.0 * 100.0
        if pct < 3.0:
            pct = 0.0
        return max(0.0, min(100.0, pct))

    def on_joy(self, msg: Joy):
        self.axes    = list(msg.axes)
        self.buttons = list(msg.buttons)

        if not self.started:
            self.started = True
            n_ax  = len(self.axes)
            n_btn = len(self.buttons)
            self.get_logger().info(f"Controller: {n_ax} axes, {n_btn} buttons")

            if n_ax >= 8:
                self.dpad_is_axes = True
                self.axis_dpad_lr = 6
                self.axis_dpad_ud = 7
            elif n_ax >= 6:
                self.dpad_is_axes = True
                self.axis_dpad_lr = 4
                self.axis_dpad_ud = 5
            else:
                self.dpad_is_axes = False

        if not self.dpad_is_axes:
            if self.prev_buttons and len(self.prev_buttons) == len(self.buttons):
                for i in range(len(self.buttons)):
                    if self.buttons[i] and not self.prev_buttons[i]:
                        self._on_dpad_press(i)
            self.prev_buttons = list(self.buttons)

        if self.dpad_is_axes and len(self.axes) > max(self.axis_dpad_lr, self.axis_dpad_ud):
            lr = self.axes[self.axis_dpad_lr]
            ud = self.axes[self.axis_dpad_ud]
            pl, pu = self.prev_dpad_axis

            if   ud >  0.5 and pu <=  0.5: self._on_dpad_press(self.dpad_up)
            elif ud < -0.5 and pu >= -0.5: self._on_dpad_press(self.dpad_down)
            if   lr >  0.5 and pl <=  0.5: self._on_dpad_press(self.dpad_left)
            elif lr < -0.5 and pl >= -0.5: self._on_dpad_press(self.dpad_right)

            self.prev_dpad_axis = [lr, ud]
            self._send_arm_a(lr, ud)

        # Right stick -> Arm B
        self._send_arm_b()

        self._send_drive()

    def _on_dpad_press(self, b):
        t = time.time()

        if b == self.dpad_up and self.btn(self.spd_btn):
            old = self.speed
            self.speed = min(self.speed + self.spd_step, self.max_spd)
            if self.speed != old:
                self.last_action      = f"Speed: {old:.2f} -> {self.speed:.2f} m/s"
                self.last_action_time = t

        elif b == self.dpad_down and self.btn(self.spd_btn):
            old = self.speed
            self.speed = max(self.speed - self.spd_step, self.min_spd)
            if self.speed != old:
                self.last_action      = f"Speed: {old:.2f} -> {self.speed:.2f} m/s"
                self.last_action_time = t

        elif b == self.dpad_right and self.btn(self.turn_btn):
            old = self.turn
            self.turn = min(self.turn + self.trn_step, self.max_trn)
            if self.turn != old:
                self.last_action      = f"Turn: {old:.2f} -> {self.turn:.2f} rad/s"
                self.last_action_time = t

        elif b == self.dpad_left and self.btn(self.turn_btn):
            old = self.turn
            self.turn = max(self.turn - self.trn_step, self.min_trn)
            if self.turn != old:
                self.last_action      = f"Turn: {old:.2f} -> {self.turn:.2f} rad/s"
                self.last_action_time = t

    def _send_arm_a(self, raw_x, raw_y):
        """D-pad -> SV;A;x;y!"""
        if self.btn(self.spd_btn) or self.btn(self.turn_btn):
            cmd_str = "SV;A;0;0!"
            if cmd_str != self.last_arm_a_cmd:
                msg = String()
                msg.data = cmd_str
                self.arm_pub.publish(msg)
                self.last_arm_a_cmd = cmd_str
            return

        if self.invert_x: raw_x = -raw_x
        if self.invert_y: raw_y = -raw_y

        sv_x = 1 if raw_x > 0.5 else (-1 if raw_x < -0.5 else 0)
        sv_y = 1 if raw_y > 0.5 else (-1 if raw_y < -0.5 else 0)

        cmd_str = f"SV;A;{sv_x};{sv_y}!"
        if cmd_str != self.last_arm_a_cmd:
            msg = String()
            msg.data = cmd_str
            self.arm_pub.publish(msg)
            self.last_arm_a_cmd = cmd_str

    def _send_arm_b(self):
        """Right stick -> SV;B;x;y!"""
        rx = self.axis(self.axis_rx)
        ry = self.axis(self.axis_ry)

        dz = self.rstick_deadzone

        sv_x = 0
        sv_y = 0

        if rx > dz:
            sv_x = 1
        elif rx < -dz:
            sv_x = -1

        if ry > dz:
            sv_y = 1
        elif ry < -dz:
            sv_y = -1

        cmd_str = f"SV;B;{sv_x};{sv_y}!"
        if cmd_str != self.last_arm_b_cmd:
            msg = String()
            msg.data = cmd_str
            self.arm_pub.publish(msg)
            self.last_arm_b_cmd = cmd_str

    def _send_drive(self):
        m = Twist()
        if self.btn(self.enable_btn):
            rt = self.trig_pct(self.axis_rt)
            lt = self.trig_pct(self.axis_lt)
            m.linear.x  = ((rt - lt) / 100.0) * self.speed
            m.angular.z = self.axis(self.axis_lx) * self.turn
        self.cmd = m
        self.drive_pub.publish(m)

    def draw(self):
        t = self.tui

        icon   = "🟢" if self.jetson_reachable else "🔴"
        status = "JETSON: CONNECTED" if self.jetson_reachable else "JETSON: NOT CONNECTED"

        if not self.axes:
            t.hline("╔", "╗")
            t.row("ROVER + ARM  |  GameSir Nova Lite")
            t.hline("╠", "╣")
            t.row(f"  {icon} {status}")
            t.hline("╠", "╣")
            t.row("  Waiting for controller input ...")
            t.blank()
            t.row("  - Is the GameSir Nova Lite powered on?")
            t.row("  - Press any button to wake it up")
            t.row("  - Run in another terminal:")
            t.row("    ros2 run joy joy_node")
            t.blank()
            dots = "." * (int(time.time() * 2) % 4)
            t.row(f"  Listening on /joy {dots:<4s}")
            t.blank()
            t.hline("╚", "╝")
            t.flush()
            return

        en     = self.btn(self.enable_btn)
        rt     = self.trig_pct(self.axis_rt)
        lt     = self.trig_pct(self.axis_lt)
        lx_pct = self.axis(self.axis_lx) * 100.0
        rx_pct = self.axis(self.axis_rx) * 100.0
        ry_pct = self.axis(self.axis_ry) * 100.0

        t.hline("╔", "╗")
        t.row("ROVER + ARM  |  GameSir Nova Lite")
        t.hline("╠", "╣")
        t.row(f"  {icon} {status}")
        t.hline("╠", "╣")
        t.row(f"Speed: {self.speed:.2f} m/s  |  Turn: {self.turn:.2f} rad/s")
        t.row(f"Drive topic : /{os.environ.get('OUTPUT_TOPIC', 'cmd_vel_teleop')}")
        t.row(f"Arm topic   : {os.environ.get('ARM_CMD_TOPIC', '/arm_cmd')}")
        t.row(
            f"Linear: {self.cmd.linear.x:>+6.2f} m/s  |"
            f"  Angular: {self.cmd.angular.z:>+6.2f} rad/s"
        )
        t.row(f"Arm A (dpad) : {self.last_arm_a_cmd or '---'}")
        t.row(f"Arm B (stick): {self.last_arm_b_cmd or '---'}")

        t.hline("╠", "╣")
        t.row("TRIGGERS (0-100%)")
        t.row(f"  RT Fwd    {tbar(rt)}")
        t.row(f"  LT Rev    {tbar(lt)}")

        t.hline("╠", "╣")
        t.row("LEFT STICK (Driving)")
        t.row(f"  X-Axis    {sbar(lx_pct)}")

        t.hline("╠", "╣")
        t.row("RIGHT STICK (Arm B)")
        t.row(f"  X-Axis    {sbar(rx_pct)}")
        t.row(f"  Y-Axis    {sbar(ry_pct)}")

        t.hline("╠", "╣")
        t.row("BUTTONS")
        for i in range(len(self.buttons)):
            name  = BTN_NAMES[i] if i < len(BTN_NAMES) else f"B{i}"
            state = "■ ON " if self.btn(i) else "□ OFF"
            mk = ""
            if i == self.enable_btn:
                mk = " ◄ SAFETY (DRIVE)"
            elif i == self.spd_btn and self.btn(i):
                mk = " ◄ HOLD+DPAD UD=SPEED"
            elif i == self.turn_btn and self.btn(i):
                mk = " ◄ HOLD+DPAD LR=TURN"
            t.row(f"  {name:<8s} {state}{mk}")

        if self.dpad_is_axes and len(self.axes) > max(self.axis_dpad_lr, self.axis_dpad_ud):
            t.hline("╠", "╣")
            t.row("D-PAD (Arm A)")
            lr = self.axes[self.axis_dpad_lr]
            ud = self.axes[self.axis_dpad_ud]

            lr_txt = "LEFT"  if lr >  0.5 else ("RIGHT" if lr < -0.5 else "---")
            ud_txt = "UP"    if ud >  0.5 else ("DOWN"  if ud < -0.5 else "---")

            if self.btn(self.spd_btn):
                if ud_txt == "UP":   ud_txt = "UP   ◄ SPEED+"
                if ud_txt == "DOWN": ud_txt = "DOWN ◄ SPEED-"
            elif self.btn(self.turn_btn):
                if lr_txt == "RIGHT": lr_txt = "RIGHT ◄ TURN+"
                if lr_txt == "LEFT":  lr_txt = "LEFT  ◄ TURN-"
            else:
                if lr_txt != "---": lr_txt += " ◄ ARM A"
                if ud_txt != "---": ud_txt += " ◄ ARM A"

            t.row(f"  Up/Down:    {ud_txt}")
            t.row(f"  Left/Right: {lr_txt}")

        t.hline("╠", "╣")
        if not self.jetson_reachable:
            t.row("  🔴 ROVER NOT CONNECTED")
            t.row(f"     Cannot reach {self.jetson_ip}")
        elif en:
            t.blank()
            t.row("  ========================================")
            t.row("          ROVER IS LIVE")
            t.row("  ========================================")
            t.blank()
        else:
            t.row("  SAFETY RELEASED - ROVER DISABLED")

        t.hline("╠", "╣")
        if self.last_action and (time.time() - self.last_action_time < 3.0):
            t.row(f"  >> {self.last_action}")
        else:
            t.row("  A+DpadUD=Speed  X+DpadLR=Turn  LB=Drive")
            t.row("  D-pad=Arm A  RightStick=Arm B")

        t.hline("╚", "╝")
        t.flush()

    def destroy_node(self):
        self.ping_thread_running = False
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CombinedTeleop()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if rclpy.ok():
                node.drive_pub.publish(Twist())
                node.destroy_node()
                rclpy.shutdown()
        except Exception:
            pass
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()