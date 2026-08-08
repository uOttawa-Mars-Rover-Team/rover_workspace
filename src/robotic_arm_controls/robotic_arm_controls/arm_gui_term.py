#!/usr/bin/python3
"""
ARM GUI — terminal edition (Arm_V2_2 target).

Box-drawing full-redraw monitor + command console for the manual joint-space arm,
in the house F710 rendering style. Publishes std_msgs/String on /arm_cmd; m_router
forwards it to the arm Mega over serial (9600). v1 mirrors commanded state — it
does NOT read back real hardware feedback (m_router only logs f;/g; today).

Wire grammar (see arm_translation / Arm_V2_2_Controls_SPI):
  S;<TW>;<EL>;<SL>;<WP>;<WR>;<EE>;!   per-joint velocity multipliers
  set0;! zero  ·  v;! verbose  ·  stepper1..4;! driver enable

Joints (enum order): TW, EL(L1), SL(L2), WP, WR, EE.

Keys (hotkey mode):
  1 2 3 4   toggle stepper1..4 enable (TW WP WR EE)
  v         toggle verbose
  :         serial-prompt typing mode
  q         quit (sends set0;! first)

Serial-prompt mode (after ':'):
  type text, ENTER sends it on /arm_cmd ('!' auto-appended), ESC cancels.
  UP/DOWN cycles through command history.
  LEFT/RIGHT move within the line, BACKSPACE edits at cursor.
"""

import os
import select
import sys
import termios
import time
import tty

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from robotic_arm_controls import arm_translation as proto

W = 54

JOINT_LABELS = {
    "TW": "TW",
    "EL": "L1/EL",
    "SL": "L2/SL",
    "WP": "WP",
    "WR": "WR",
    "EE": "EE",
}


def row(text):
    return f"║ {text:<{W}} ║"


def hline(left, right, fill="═"):
    return left + fill * (W + 2) + right


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


class ArmTermGui(Node):
    def __init__(self, node_name: str = "arm_gui_term"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        topic = os.environ.get("ARM_CMD_TOPIC", "arm_cmd")
        self.pub = self.create_publisher(String, f"/{topic}", 20)
        self.sub = self.create_subscription(String, f"/{topic}", self.on_arm_cmd, 20)
        self.topic = topic

        self.rx_count = 0
        self.jv = {j: 0.0 for j in proto.JOINT_IDS}
        self.steppers = {1: False, 2: False, 3: False, 4: False}
        self.verbose = False

        self.typing = False
        self.buffer = ""
        self.cursor = 0
        self.history = []
        self.history_idx = None
        self.history_edit = ""

        self.log = []
        self.LOG_ROWS = 3

        self.last_action = ""
        self.last_action_time = 0.0
        self.running = True
        self._first_draw = True

        self.stdin_fd = sys.stdin.fileno()

        self.timer = self.create_timer(1.0 / 30.0, self.draw)
        self.input_timer = self.create_timer(1.0 / 60.0, self.poll_input)

    def send(self, frame: str, label: str = ""):
        msg = String()
        msg.data = frame
        self.pub.publish(msg)
        if label:
            self.toast(label)

    def toast(self, text: str):
        self.last_action = text
        self.last_action_time = time.time()

    def zero_velocities(self):
        self.send(proto.set_velocities([0.0] * len(proto.JOINT_IDS)), "zero velocities")

    def on_arm_cmd(self, msg: String):
        frame = msg.data
        self.rx_count += 1
        stamp = time.strftime("%H:%M:%S")
        self.log.append(f"{stamp}  {frame[:W - 4]}")
        self.log = self.log[-200:]

        info = proto.parse(frame)
        t = info["type"]
        if t == "S":
            vels = info["velocities"]
            for i, j in enumerate(proto.JOINT_IDS):
                self.jv[j] = round(vels[i], 2) if i < len(vels) else 0.0
        elif t == "set0":
            for j in self.jv:
                self.jv[j] = 0.0
        elif t == "v":
            self.verbose = not self.verbose
        elif t == "stepper":
            n = info["n"]
            if n in self.steppers:
                self.steppers[n] = not self.steppers[n]

    def poll_input(self):
        try:
            r, _, _ = select.select([self.stdin_fd], [], [], 0)
            if not r:
                return
            data = os.read(self.stdin_fd, 64).decode(errors="ignore")
        except Exception as exc:
            self.get_logger().warn(f"stdin poll error: {exc}")
            return

        for tok in self._parse(data):
            try:
                if self.typing:
                    self._key_typing(tok)
                else:
                    self._key_hotkey(tok)
            except Exception as exc:
                self.get_logger().warn(f"key handler error: {exc}")
   
    @staticmethod
    def _parse(data: str):
        arrows = {
            "\x1b[A": "UP",
            "\x1b[B": "DOWN",
            "\x1b[C": "RIGHT",
            "\x1b[D": "LEFT",
            "\x1b[H": "HOME",
            "\x1b[F": "END",
            "\x1b[3~": "DELETE",
        }
        tokens = []
        i = 0
        while i < len(data):
            c = data[i]
            if c == "\x1b":
                matched = False
                for seq, name in sorted(arrows.items(), key=lambda x: -len(x[0])):
                    if data.startswith(seq, i):
                        tokens.append(name)
                        i += len(seq)
                        matched = True
                        break
                if matched:
                    continue
                tokens.append("ESC")
            elif c in ("\r", "\n"):
                tokens.append("ENTER")
            elif c in ("\x7f", "\x08"):
                tokens.append("BACKSPACE")
            else:
                tokens.append(("CHAR", c))
            i += 1
        return tokens
    
    def _exit_history_mode(self):
        if self.history_idx is not None:
            self.buffer = self.history_edit
            self.cursor = len(self.buffer)
            self.history_idx = None
            self.history_edit = ""

    def _key_typing(self, tok):
        if tok == "ENTER":
            text = self.buffer.strip()
            self.typing = False
            self.history_idx = None
            self.history_edit = ""
            self.buffer = ""
            self.cursor = 0
            if text:
                self.history.append(text)
                self.send(proto.raw(text), f"serial: {text}")

        elif tok == "ESC":
            self.typing = False
            self.history_idx = None
            self.history_edit = ""
            self.buffer = ""
            self.cursor = 0
            self.toast("serial prompt cancelled")

        elif tok == "BACKSPACE":
            self._exit_history_mode()
            if self.cursor > 0:
                self.buffer = self.buffer[:self.cursor - 1] + self.buffer[self.cursor:]
                self.cursor -= 1

        elif tok == "DELETE":
            self._exit_history_mode()
            if self.cursor < len(self.buffer):
                self.buffer = self.buffer[:self.cursor] + self.buffer[self.cursor + 1:]

        elif tok == "LEFT":
            if self.cursor > 0:
                self.cursor -= 1

        elif tok == "RIGHT":
            if self.cursor < len(self.buffer):
                self.cursor += 1

        elif tok == "HOME":
            self.cursor = 0

        elif tok == "END":
            self.cursor = len(self.buffer)

        elif tok == "UP":
            if self.history:
                if self.history_idx is None:
                    self.history_edit = self.buffer
                    self.history_idx = len(self.history) - 1
                elif self.history_idx > 0:
                    self.history_idx -= 1
                self.buffer = self.history[self.history_idx]
                self.cursor = len(self.buffer)

        elif tok == "DOWN":
            if self.history_idx is not None:
                if self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.buffer = self.history[self.history_idx]
                else:
                    self.history_idx = None
                    self.buffer = self.history_edit
                    self.history_edit = ""
                self.cursor = len(self.buffer)

        elif isinstance(tok, tuple) and tok[0] == "CHAR":
            self._exit_history_mode()
            self.buffer = self.buffer[:self.cursor] + tok[1] + self.buffer[self.cursor:]
            self.cursor += 1

    def _key_typing(self, tok):
        if tok == "ENTER":
            text = self.buffer.strip()
            self.typing = False
            self.history_idx = None
            self.history_edit = ""
            self.buffer = ""
            self.cursor = 0
            if text:
                self.history.append(text)
                self.send(proto.raw(text), f"serial: {text}")

        elif tok == "ESC":
            self.typing = False
            self.history_idx = None
            self.history_edit = ""
            self.buffer = ""
            self.cursor = 0
            self.toast("serial prompt cancelled")

        elif tok == "BACKSPACE":
            self._exit_history_mode()
            if self.cursor > 0:
                self.buffer = self.buffer[:self.cursor - 1] + self.buffer[self.cursor:]
                self.cursor -= 1

        elif tok == "LEFT":
            if self.cursor > 0:
                self.cursor -= 1

        elif tok == "RIGHT":
            if self.cursor < len(self.buffer):
                self.cursor += 1

        elif tok == "UP":
            if self.history:
                if self.history_idx is None:
                    self.history_edit = self.buffer
                    self.history_idx = len(self.history) - 1
                elif self.history_idx > 0:
                    self.history_idx -= 1
                self.buffer = self.history[self.history_idx]
                self.cursor = len(self.buffer)

        elif tok == "DOWN":
            if self.history_idx is not None:
                if self.history_idx < len(self.history) - 1:
                    self.history_idx += 1
                    self.buffer = self.history[self.history_idx]
                    self.cursor = len(self.buffer)
                else:
                    self.history_idx = None
                    self.buffer = self.history_edit
                    self.history_edit = ""
                    self.cursor = len(self.buffer)

        elif isinstance(tok, tuple) and tok[0] == "CHAR":
            if self.history_idx is not None:
                self.buffer = self.history_edit
                self.cursor = len(self.buffer)
                self.history_idx = None
                self.history_edit = ""
            self.buffer = self.buffer[:self.cursor] + tok[1] + self.buffer[self.cursor:]
            self.cursor += 1

    def _key_hotkey(self, tok):
        if not (isinstance(tok, tuple) and tok[0] == "CHAR"):
            return

        ch = tok[1]

        if ch in ("1", "2", "3", "4"):
            n = int(ch)
            self.send(proto.toggle_stepper(n), f"stepper{n} ({proto.STEPPERS[n]})")
        elif ch == "v":
            self.send(proto.toggle_verbose(), "verbose toggle")
        elif ch == ":":
            self.typing = True
            self.buffer = ""
            self.cursor = 0
            self.history_idx = None
            self.history_edit = ""
            self.toast("serial prompt: type, ENTER=send, ESC=cancel")
        elif ch == "q":
            self.running = False

    def stepper_diamond(self):
        def cell(n):
            jid = proto.STEPPERS[n]
            mark = "\u25c6" if self.steppers[n] else "\u25c7"
            return f"{mark} {jid}"

        c = W // 2
        top = cell(2).center(W)
        mid = f"{cell(1):<{c}}{cell(3):>{W - c}}"
        bot = cell(4).center(W)
        return [top, mid, bot]

    def draw(self):
        vb = "ON" if self.verbose else "OFF"

        lines = [hline("╔", "╗")]
        lines.append(row(f"ARM GUI   Mode:ARM   Vb:{vb}"))
        lines.append(hline("╠", "╣"))
        lines.append(row(f"Bus /{self.topic}   rx: {self.rx_count}"))
        lines.append(hline("╠", "╣"))
        for j in proto.JOINT_IDS:
            v = self.jv[j]
            label = JOINT_LABELS.get(j, j)
            lines.append(row(f"  {label:<6}{sbar(v, 1.0)} {v:>+6.2f}"))
        lines.append(hline("╠", "╣"))
        for dline in self.stepper_diamond():
            lines.append(row(dline))
        lines.append(hline("╠", "╣"))
        recent = self.log[-self.LOG_ROWS:]
        for _ in range(self.LOG_ROWS - len(recent)):
            lines.append(row(""))
        for entry in recent:
            lines.append(row(f"  {entry[:W - 2]}"))
        lines.append(hline("╠", "╣"))
        if self.typing:
            shown = self.buffer[:self.cursor] + "|" + self.buffer[self.cursor:]
            lines.append(row(f"  serial> {shown[:W - 11]}"))
        elif self.last_action and (time.time() - self.last_action_time < 3.0):
            lines.append(row(f"  >> {self.last_action[:W - 5]}"))
        else:
            lines.append(row("  1-4 step  v vrb  : serial  q quit"))
        lines.append(hline("╚", "╝"))

        out = "\033[2J" if self._first_draw else ""
        self._first_draw = False
        out += "\033[H" + "".join(l + "\033[K\n" for l in lines[:-1])
        out += lines[-1] + "\033[K\033[J"
        sys.stdout.write(out)
        sys.stdout.flush()


def main(args=None):
    rclpy.init(args=args)

    fd = sys.stdin.fileno()
    old_termios = None
    try:
        old_termios = termios.tcgetattr(fd)
        tty.setcbreak(fd)
    except (termios.error, ValueError) as exc:
        print(
            f"[arm_gui] cbreak setup FAILED: {exc}\n"
            f"[arm_gui] stdin is not a real TTY — keys will NOT be read. "
            f"Run this script directly in an interactive terminal.",
            file=sys.stderr,
            flush=True,
        )

    node = ArmTermGui()
    try:
        while rclpy.ok() and node.running:
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            if rclpy.ok():
                zero = String()
                node.pub.publish(zero)
                node.destroy_node()
                rclpy.shutdown()
        except Exception:
            pass
        if old_termios is not None:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_termios)
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
