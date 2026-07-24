#!/usr/bin/python3
"""
MSERVO GUI — terminal edition (Arm_V2_2 target).

Box-drawing full-redraw monitor + command console for the manual joint-space arm,
in the house F710 rendering style. Publishes std_msgs/String on /arm_cmd; m_router
forwards it to the arm Mega over serial (9600). v1 mirrors commanded state — it
does NOT read back real hardware feedback (m_router only logs f;/g; today).

Wire grammar (see mservo_protocol / Arm_V2_2_Controls_SPI):
  S;<TW>;<WP>;<WR>;<EE>;<SL>;<EL>;!   per-joint velocity multipliers
  set0;! zero  ·  stop;! e-stop  ·  v;! verbose  ·  stepper1..4;! driver enable
  svu;!/svd;!/svs;! camera servo

Joints (enum order): TW tower, WP wrist-pitch, WR wrist-roll, EE end-effector
(steppers) · SL shoulder, EL elbow (linear actuators).

Keys (hotkey mode) — lowercase = toward MIN (−speed), UPPERCASE = toward MAX (+speed):
  a/A TW    s/S WP    d/D WR    f/F EE    g/G SL    h/H EL
  0         zero all joint velocities (send S; all 0)     SPACE  E-STOP (stop;!)
  1 2 3 4   toggle stepper1..4 enable (TW WP WR EE)        k      set0;! (zero enc)
  ↑ / ↓     speed scalar +/-                               v      toggle verbose
  u/j/n     camera servo up / stop / down
  m         switch mode label (SERVO/ARM, display only)
  :         serial-prompt typing mode        q  quit (sends set0;! first)

Serial-prompt mode (after ':'):
  type text, ENTER sends it on /arm_cmd ('!' auto-appended), ESC cancels.
"""

import os
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pynput import keyboard

from robotic_arm_controls import mservo_protocol as proto

W = 54

# joint id -> the lowercase jog key (uppercase of the same key = +direction)
JOINT_KEYS = {"a": "TW", "s": "WP", "d": "WR", "f": "EE", "g": "SL", "h": "EL"}


def row(text):
    return f"║ {text:<{W}} ║"


def hline(left, right, fill="═"):
    return left + fill * (W + 2) + right


def tbar(pct, w=20):
    f = int(max(0.0, min(100.0, pct)) / 100.0 * w)
    return f"[{'#' * f}{'.' * (w - f)}] {pct:>5.1f}%"


def sbar(v, vmax, w=12):
    """Signed centered bar for a joint velocity in [-vmax, +vmax]."""
    c = w // 2
    if vmax <= 0:
        frac = 0.0
    else:
        frac = max(-1.0, min(1.0, v / vmax))
    f = int(abs(frac) * c)
    if frac > 0:
        return f"[{'.' * c}|{'#' * f}{'.' * (c - f)}]"
    if frac < 0:
        return f"[{'.' * (c - f)}{'#' * f}|{'.' * c}]"
    return f"[{'.' * c}|{'.' * c}]"


class MservoTermGui(Node):

    MODES = ("SERVO", "ARM")

    def __init__(self, node_name: str = "mservo_gui_term"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        topic = os.environ.get("ARM_CMD_TOPIC", "arm_cmd")
        self.pub = self.create_publisher(String, f"/{topic}", 20)
        self.topic = topic

        # Mirrored state (what we've commanded — not hardware truth).
        self.jv = {j: 0.0 for j in proto.JOINT_IDS}   # per-joint velocity mult.
        self.steppers = {1: False, 2: False, 3: False, 4: False}
        self.speed = 0.7           # scalar magnitude in [0.4, 1.0]
        self.spd_step = 0.1
        self.mode_idx = 1          # index into MODES; display-only label
        self.verbose = False
        self.estopped = False
        self.camera = "stop"       # up / down / stop

        # Serial-prompt line editor.
        self.typing = False
        self.buffer = ""

        # Scrolling command log.
        self.log = []
        self.LOG_ROWS = 3

        self.last_action = ""
        self.last_action_time = 0.0
        self.running = True
        self._first_draw = True

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.timer = self.create_timer(1.0 / 30.0, self.draw)

    # ── Command dispatch ─────────────────────────────────────────────────────

    def send(self, frame: str, label: str = ""):
        msg = String()
        msg.data = frame
        self.pub.publish(msg)
        stamp = time.strftime("%H:%M:%S")
        self.log.append(f"{stamp}  ->  {frame}")
        self.log = self.log[-200:]
        if label:
            self.toast(label)

    def toast(self, text: str):
        self.last_action = text
        self.last_action_time = time.time()

    def send_joints(self, label: str = ""):
        self.send(proto.set_velocities([self.jv[j] for j in proto.JOINT_IDS]), label)

    def jog(self, joint: str, sign: int):
        self.estopped = False
        self.jv[joint] = round(sign * self.speed, 2)
        self.send_joints(f"{joint} -> {'MAX' if sign > 0 else 'MIN'} ({self.jv[joint]:+.2f})")

    def zero_velocities(self):
        for j in self.jv:
            self.jv[j] = 0.0
        self.send_joints("all joints velocity 0")

    def reapply_speed(self):
        # Rescale any active joints to the new speed magnitude.
        changed = False
        for j, v in self.jv.items():
            if v != 0.0:
                self.jv[j] = round((1 if v > 0 else -1) * self.speed, 2)
                changed = True
        if changed:
            self.send_joints(f"speed -> {self.speed:.2f}")

    # ── Keyboard handling ────────────────────────────────────────────────────

    def on_press(self, key):
        try:
            if self.typing:
                self._on_press_typing(key)
            else:
                self._on_press_hotkey(key)
        except Exception as exc:  # never let a stray key kill the listener thread
            self.get_logger().warn(f"key handler error: {exc}")

    def _on_press_typing(self, key):
        if key == keyboard.Key.enter:
            text = self.buffer.strip()
            self.typing = False
            self.buffer = ""
            if text:
                self.send(proto.raw(text), f"serial: {text}")
        elif key == keyboard.Key.esc:
            self.typing = False
            self.buffer = ""
            self.toast("serial prompt cancelled")
        elif key == keyboard.Key.backspace:
            self.buffer = self.buffer[:-1]
        elif key == keyboard.Key.space:
            self.buffer += " "
        else:
            ch = getattr(key, "char", None)
            if ch is not None:
                self.buffer += ch

    def _on_press_hotkey(self, key):
        if key == keyboard.Key.space:
            self.estopped = True
            for j in self.jv:
                self.jv[j] = 0.0
            self.send(proto.estop(), "E-STOP")
            return
        if key == keyboard.Key.up:
            old = self.speed
            self.speed = round(min(self.speed + self.spd_step, 1.0), 2)
            if self.speed != old:
                self.reapply_speed()
                self.toast(f"speed {old:.2f} -> {self.speed:.2f}")
            return
        if key == keyboard.Key.down:
            old = self.speed
            self.speed = round(max(self.speed - self.spd_step, 0.4), 2)
            if self.speed != old:
                self.reapply_speed()
                self.toast(f"speed {old:.2f} -> {self.speed:.2f}")
            return

        ch = getattr(key, "char", None)
        if ch is None:
            return

        # Joint jog: lowercase = -speed, uppercase = +speed.
        low = ch.lower()
        if low in JOINT_KEYS:
            joint = JOINT_KEYS[low]
            self.jog(joint, +1 if ch.isupper() else -1)
            return

        if ch in ("1", "2", "3", "4"):
            n = int(ch)
            self.steppers[n] = not self.steppers[n]
            self.send(proto.toggle_stepper(n),
                      f"stepper{n} ({proto.STEPPERS[n]}) -> "
                      f"{'ON' if self.steppers[n] else 'OFF'}")
        elif ch == "0":
            self.zero_velocities()
        elif ch == "k":
            self.estopped = False
            self.send(proto.zero_all(), "set0 (zero encoders)")
        elif ch == "v":
            self.verbose = not self.verbose
            self.send(proto.toggle_verbose(), f"verbose -> {self.verbose}")
        elif ch == "u":
            self.camera = "up"
            self.send(proto.camera_servo("up"), "camera servo up")
        elif ch == "n":
            self.camera = "down"
            self.send(proto.camera_servo("down"), "camera servo down")
        elif ch == "j":
            self.camera = "stop"
            self.send(proto.camera_servo("stop"), "camera servo stop")
        elif ch == "m":
            self.mode_idx = (self.mode_idx + 1) % len(self.MODES)
            self.toast(f"mode label -> {self.MODES[self.mode_idx]}")
        elif ch == ":":
            self.typing = True
            self.buffer = ""
            self.toast("serial prompt: type, ENTER=send, ESC=cancel")
        elif ch == "q":
            self.running = False

    # ── Rendering ──────────────────────────────────────────────────────────────

    def stepper_diamond(self):
        """4 steppers as a diamond: TW top, WP right, WR bottom, EE left."""
        def cell(n):
            jid = proto.STEPPERS[n]
            mark = "\u25c6" if self.steppers[n] else "\u25c7"  # ◆ on / ◇ off
            return f"{mark} {jid}"

        c = W // 2
        top = cell(1).center(W)
        mid = f"{cell(4):<{c}}{cell(2):>{W - c}}"
        bot = cell(3).center(W)
        return [top, mid, bot]

    def draw(self):
        mode = self.MODES[self.mode_idx]
        vb = "ON" if self.verbose else "OFF"

        lines = [hline("╔", "╗")]
        lines.append(row(f"MSERVO ARM GUI   Mode:{mode}   Cam:{self.camera.upper()}  Vb:{vb}"))
        lines.append(hline("╠", "╣"))
        lines.append(row(f"Speed  {tbar(self.speed * 100.0)}"))
        lines.append(hline("╠", "╣"))
        for j in proto.JOINT_IDS:
            v = self.jv[j]
            lines.append(row(f"  {j:<3}{sbar(v, self.speed)} {v:>+6.2f}"))
        lines.append(hline("╠", "╣"))
        for dline in self.stepper_diamond():
            lines.append(row(dline))
        lines.append(hline("╠", "╣"))
        if self.estopped:
            lines.append(row("  ****  E-STOP  (k = set0 to clear)  ****"))
        else:
            lines.append(row("  ARMED    SPACE = E-STOP    0 = zero vel"))
        lines.append(hline("╠", "╣"))
        recent = self.log[-self.LOG_ROWS:]
        for _ in range(self.LOG_ROWS - len(recent)):
            lines.append(row(""))
        for entry in recent:
            lines.append(row(f"  {entry[:W - 2]}"))
        lines.append(hline("╠", "╣"))
        if self.typing:
            lines.append(row(f"  serial> {self.buffer[:W - 11]}\u2588"))
        elif self.last_action and (time.time() - self.last_action_time < 3.0):
            lines.append(row(f"  >> {self.last_action[:W - 5]}"))
        else:
            lines.append(row("  a/s/d/f/g/h jog  1-4 step  v vrb  u/j/n cam  : q"))
        lines.append(hline("╚", "╝"))

        # Redraw in place: home cursor, clear each line to EOL (no full-screen
        # wipe = no flicker/scroll), no trailing newline, then clear below in
        # case a previous frame was taller.
        out = "\033[2J" if self._first_draw else ""
        self._first_draw = False
        out += "\033[H" + "".join(l + "\033[K\n" for l in lines[:-1])
        out += lines[-1] + "\033[K\033[J"
        sys.stdout.write(out)
        sys.stdout.flush()


def main(args=None):
    rclpy.init(args=args)
    node = MservoTermGui()
    try:
        while rclpy.ok() and node.running:
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            node.listener.stop()
            if rclpy.ok():
                zero = String()
                zero.data = proto.zero_all()
                node.pub.publish(zero)
                node.destroy_node()
                rclpy.shutdown()
        except Exception:
            pass
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
