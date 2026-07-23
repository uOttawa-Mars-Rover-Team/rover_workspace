#!/usr/bin/python3
"""
MSERVO GUI — terminal edition (AppGNC target).

Box-drawing full-redraw monitor + command console for the AppGNC servo demo, in
the house F710 rendering style. Publishes std_msgs/String on /arm_cmd; m_router
forwards it to the GNC Mega over serial. v1 mirrors commanded state — it does NOT
read back real hardware feedback.

Wire grammar (see mservo_protocol / MSERVO_DEMO.md):
  SV;<id>;<v0>[;<v1>]!   A=pan/tilt (2-axis), B, C (1-axis); dir in {-1,0,+1}
  GNC;move;1! / GNC;move;-1! / GNC;stop! / GNC;update!

Keys (hotkey mode):
  ← / →     Servo A  pan  -1 / +1        ↑ / ↓   Servo A tilt +1 / -1
  f / g     Servo B  -1 / +1             h / j   Servo C  -1 / +1
  z x c     stop servo A / B / C
  r / m     GNC move  reverse / forward  u       GNC update
  SPACE     ALL STOP (all servos + GNC stop)
  :         enter serial-prompt typing mode
  q         quit (sends ALL STOP first)

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


def row(text):
    return f"║ {text:<{W}} ║"


def hline(left, right, fill="═"):
    return left + fill * (W + 2) + right


def sdir(d):
    """Discrete signed direction indicator: ◀ (min) · 0 · ▶ (max)."""
    lo = "\u25c0" if d < 0 else "\u00b7"   # ◀ / ·
    mid = "0" if d == 0 else "\u00b7"
    hi = "\u25b6" if d > 0 else "\u00b7"   # ▶ / ·
    return f"{lo}   {mid}   {hi}"


def servo_label(d):
    return "\u2192 MAX" if d > 0 else "\u2192 MIN" if d < 0 else "STOP"


def gnc_label(d):
    return "FWD" if d > 0 else "REV" if d < 0 else "STOP"


class MservoTermGui(Node):

    def __init__(self, node_name: str = "mservo_gui_term"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        topic = os.environ.get("ARM_CMD_TOPIC", "arm_cmd")
        self.pub = self.create_publisher(String, f"/{topic}", 20)
        self.topic = topic

        # Mirrored state (what we've commanded — not hardware truth).
        # Servo A is 2-axis (pan, tilt); B and C are 1-axis.
        self.servo = {
            "A": {"pan": 0, "tilt": 0},
            "B": {"axis": 0},
            "C": {"axis": 0},
        }
        self.gnc = 0  # -1 reverse / 0 stop / +1 forward

        # Serial-prompt line editor.
        self.typing = False
        self.buffer = ""

        # Scrolling command log.
        self.log = []
        self.LOG_ROWS = 8

        self.last_action = ""
        self.last_action_time = 0.0
        self.running = True

        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.timer = self.create_timer(1.0 / 15.0, self.draw)

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

    def send_servo_a(self, label=""):
        self.send(proto.servo("A", self.servo["A"]["pan"], self.servo["A"]["tilt"]),
                  label)

    def all_stop(self):
        self.servo["A"] = {"pan": 0, "tilt": 0}
        self.servo["B"]["axis"] = 0
        self.servo["C"]["axis"] = 0
        self.gnc = 0
        self.send(proto.servo("A", 0, 0))
        self.send(proto.servo("B", 0))
        self.send(proto.servo("C", 0))
        self.send(proto.gnc_stop(), "ALL STOP")

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
        # Servo A (2-axis) on the arrow keys.
        if key == keyboard.Key.left:
            self.servo["A"]["pan"] = -1
            self.send_servo_a("A pan -> MIN")
            return
        if key == keyboard.Key.right:
            self.servo["A"]["pan"] = 1
            self.send_servo_a("A pan -> MAX")
            return
        if key == keyboard.Key.up:
            self.servo["A"]["tilt"] = 1
            self.send_servo_a("A tilt -> MAX")
            return
        if key == keyboard.Key.down:
            self.servo["A"]["tilt"] = -1
            self.send_servo_a("A tilt -> MIN")
            return
        if key == keyboard.Key.space:
            self.all_stop()
            return

        ch = getattr(key, "char", None)
        if ch is None:
            return

        if ch == "f":
            self.servo["B"]["axis"] = -1
            self.send(proto.servo("B", -1), "B -> MIN")
        elif ch == "g":
            self.servo["B"]["axis"] = 1
            self.send(proto.servo("B", 1), "B -> MAX")
        elif ch == "h":
            self.servo["C"]["axis"] = -1
            self.send(proto.servo("C", -1), "C -> MIN")
        elif ch == "j":
            self.servo["C"]["axis"] = 1
            self.send(proto.servo("C", 1), "C -> MAX")
        elif ch == "z":
            self.servo["A"] = {"pan": 0, "tilt": 0}
            self.send_servo_a("A stop")
        elif ch == "x":
            self.servo["B"]["axis"] = 0
            self.send(proto.servo("B", 0), "B stop")
        elif ch == "c":
            self.servo["C"]["axis"] = 0
            self.send(proto.servo("C", 0), "C stop")
        elif ch == "m":
            self.gnc = 1
            self.send(proto.gnc_move(1), "GNC forward")
        elif ch == "r":
            self.gnc = -1
            self.send(proto.gnc_move(-1), "GNC reverse")
        elif ch == "u":
            self.send(proto.gnc_update(), "GNC update requested")
        elif ch == ":":
            self.typing = True
            self.buffer = ""
            self.toast("serial prompt: type, ENTER=send, ESC=cancel")
        elif ch == "q":
            self.running = False

    # ── Rendering ──────────────────────────────────────────────────────────────

    def draw(self):
        sys.stdout.write("\033[2J\033[H")

        a = self.servo["A"]
        b = self.servo["B"]["axis"]
        c = self.servo["C"]["axis"]

        print(hline("╔", "╗"))
        print(row("MSERVO GUI  (terminal)  ->  AppGNC"))
        print(hline("╠", "╣"))
        print(row(f"Grammar: SV;/GNC;    Topic: /{self.topic}"))

        print(hline("╠", "╣"))
        print(row("SERVO A (2-axis)                     (arrows)"))
        print(row(f"  pan    {sdir(a['pan']):<12}  {servo_label(a['pan'])}"))
        print(row(f"  tilt   {sdir(a['tilt']):<12}  {servo_label(a['tilt'])}"))
        print(row("SERVO B (1-axis)                     (f/g, x stop)"))
        print(row(f"  axis   {sdir(b):<12}  {servo_label(b)}"))
        print(row("SERVO C (1-axis)                     (h/j, c stop)"))
        print(row(f"  axis   {sdir(c):<12}  {servo_label(c)}"))

        print(hline("╠", "╣"))
        print(row(f"GNC    {sdir(self.gnc):<12}  {gnc_label(self.gnc):<5} (r/m, u update)"))

        print(hline("╠", "╣"))
        print(row("  STATUS: RUNNING    (SPACE = ALL STOP)"))

        print(hline("╠", "╣"))
        print(row("LOG  (last sent -> serial)"))
        recent = self.log[-self.LOG_ROWS:]
        pad = self.LOG_ROWS - len(recent)
        for _ in range(pad):
            print(row(""))
        for entry in recent:
            print(row(f"  {entry[:W - 2]}"))

        print(hline("╠", "╣"))
        if self.typing:
            print(row(f"  serial> {self.buffer[:W - 11]}\u2588"))
        else:
            print(row("  serial prompt: press ':'  |  q=quit"))

        print(hline("╠", "╣"))
        if self.last_action and (time.time() - self.last_action_time < 3.0):
            print(row(f"  >> {self.last_action[:W - 5]}"))
        else:
            print(row("  z/x/c stop A/B/C   SPACE all-stop   u update"))

        print(hline("╚", "╝"))
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
                for frame in (proto.servo("A", 0, 0), proto.servo("B", 0),
                              proto.servo("C", 0), proto.gnc_stop()):
                    stop = String()
                    stop.data = frame
                    node.pub.publish(stop)
                node.destroy_node()
                rclpy.shutdown()
        except Exception:
            pass
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
