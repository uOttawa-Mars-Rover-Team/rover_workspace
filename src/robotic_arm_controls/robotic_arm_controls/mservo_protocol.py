#!/usr/bin/python3
"""
mservo_protocol — single source of truth for the arm `/arm_cmd` serial grammar.

Pure functions only (no ROS, no serial). The terminal GUI (and, later, the web
GUI) build commands through here so the wire format lives in exactly one place.

Target firmware: Arm_V2_2_Controls_SPI (the manual joint-space arm, NOT IK, NOT
the AppGNC servo demo). Commands are published as std_msgs/String on `/arm_cmd`;
m_router writes the string straight to serial. The arm reads until the
terminator `!`; `\\n` is ignored on the embedded side. Baud 9600.

Grammar Arm_V2_2 processCommand() accepts (anything else -> "Unknown command!"):
  S;<TW>;<WP>;<WR>;<EE>;<SL>;<EL>;!   per-joint velocity multipliers
  set0;!    zero all joints/encoders
  stop;!    emergency stop
  v;!       toggle verbose feedback (f;.../g;...)
  stepper1..4;!   toggle TW/WP/WR/EE stepper driver enable
  svu;!/svd;!/svs;!   camera servo up / down / stop

6 joints in enum order — TW WP WR EE SL EL:
  TW tower, WP wrist-pitch, WR wrist-roll, EE end-effector (steppers),
  SL shoulder, EL elbow (linear actuators). Plus a camera servo.
"""

from typing import Sequence

# Payloads are joined with ";" and every frame ends with this terminator.
TERMINATOR = ";!"

# Joint order for the `S;...` velocity command (matches Arm_V2_2 Joint_ID enum).
JOINT_IDS = ("TW", "WP", "WR", "EE", "SL", "EL")

# Stepper-driver enable toggles: stepper1->TW, 2->WP, 3->WR, 4->EE.
STEPPERS = {1: "TW", 2: "WP", 3: "WR", 4: "EE"}


def frame(payload: str) -> str:
    """Wrap a bare payload into a serial frame. `frame("stop") -> "stop;!"`.

    Idempotent: if the payload already ends in "!" it is returned unchanged.
    """
    payload = payload.strip()
    if payload.endswith("!"):
        return payload
    return payload + TERMINATOR


# ── Arm joint / motion commands ──────────────────────────────────────────────

def set_velocities(velocities: Sequence[float]) -> str:
    """`S;<TW>;<WP>;<WR>;<EE>;<SL>;<EL>;!` — per-joint velocity multipliers.

    Expects exactly len(JOINT_IDS) values in JOINT_IDS order.
    """
    if len(velocities) != len(JOINT_IDS):
        raise ValueError(
            f"expected {len(JOINT_IDS)} velocities (order {JOINT_IDS}), "
            f"got {len(velocities)}"
        )
    fields = ";".join(str(round(float(v), 2)) for v in velocities)
    return frame(f"S;{fields}")


def zero_all() -> str:
    """`set0;!` — zero every joint velocity/position (and encoder zero)."""
    return frame("set0")


def estop() -> str:
    """`stop;!` — emergency stop."""
    return frame("stop")


def toggle_verbose() -> str:
    """`v;!` — toggle embedded verbose feedback (f;.../g;...)."""
    return frame("v")


def toggle_stepper(n: int) -> str:
    """`stepper{n};!` — toggle a stepper driver's enable line (n in 1..4)."""
    if n not in STEPPERS:
        raise ValueError(f"stepper index must be one of {sorted(STEPPERS)}, got {n}")
    return frame(f"stepper{n}")


def camera_servo(direction: str) -> str:
    """`svu;!`/`svd;!`/`svs;!` — camera servo up / down / stop."""
    mapping = {"up": "svu", "down": "svd", "stop": "svs"}
    if direction not in mapping:
        raise ValueError(f"direction must be one of {sorted(mapping)}, got {direction!r}")
    return frame(mapping[direction])


# ── Parsing (incoming /arm_cmd traffic) ──────────────────────────────────────

def parse(frame: str) -> dict:
    """Parse a frame seen on /arm_cmd into a dict describing the command.

    Used by the GUI to mirror whatever is on the bus (its own echoes, plus
    ik_joy_controls / ik_keyboard_controls commands). Positional velocity fields
    map to JOINT_IDS order (TW WP WR EE SL EL) — the order Arm_V2_2 interprets.

    Returns one of:
      {"type": "S", "velocities": [float, ...]}
      {"type": "set0" | "stop" | "v" | "svu" | "svd" | "svs"}
      {"type": "stepper", "n": int}
      {"type": "other", "head": str}
    """
    s = frame.strip()
    if s.endswith("!"):
        s = s[:-1]
    parts = s.split(";")
    head = parts[0] if parts else ""

    if head == "S":
        vels = []
        for p in parts[1:]:
            if p == "":
                continue
            try:
                vels.append(float(p))
            except ValueError:
                pass
        return {"type": "S", "velocities": vels}
    if head in ("set0", "stop", "v", "svu", "svd", "svs"):
        return {"type": head}
    if head.startswith("stepper") and head[len("stepper"):].isdigit():
        return {"type": "stepper", "n": int(head[len("stepper"):])}
    return {"type": "other", "head": head}


# ── Free-text serial prompt ──────────────────────────────────────────────────

def raw(text: str) -> str:
    """Frame arbitrary user-typed text for the serial prompt.

    Appends the terminator only if the user didn't already type one.
    """
    return frame(text)
