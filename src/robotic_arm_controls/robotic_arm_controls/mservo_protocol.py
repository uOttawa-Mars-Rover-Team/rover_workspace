#!/usr/bin/python3
"""
mservo_protocol — single source of truth for the AppGNC serial grammar.

Pure functions only (no ROS, no serial). The terminal GUI (and, later, the web
GUI) build commands through here so the wire format lives in exactly one place.

Target firmware: AppGNC (`rover_embedded_shield`, env `AppGNC`), see
`MSERVO_DEMO.md` / `MSERVO_TEST.md`. Commands are published as std_msgs/String
on `/arm_cmd`; m_router writes the string straight to serial. AppGNC reads until
the terminator `!`; `\\n`/`\\r` are ignored on the embedded side.

Grammar AppGNC actually accepts (everything else -> "[GNC] Ignored"):
  SV;<id>;<v0>[;<v1>]!   id in A/B/C, values in {-1,0,+1}
                         A = 2-axis (pan, tilt); B, C = 1-axis
                         -1 toward min, 0 stop/hold, +1 toward max
  GNC;move;1!  GNC;move;-1!  GNC;stop!  GNC;update!
"""

# AppGNC reads until this terminator. NOTE: bare "!", not the legacy ";!".
TERMINATOR = "!"

# Servo ids and their axis counts (from AppGNC.cpp handleSV()).
SERVO_IDS = ("A", "B", "C")
SERVO_AXES = {"A": 2, "B": 1, "C": 1}


def _clamp_dir(v) -> int:
    """Clamp any int-ish value to the firmware's {-1, 0, +1} direction set."""
    try:
        v = int(v)
    except (TypeError, ValueError):
        v = 0
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


# ── Servo commands ───────────────────────────────────────────────────────────

def servo(servo_id: str, v0, v1=None) -> str:
    """`SV;<id>;<v0>[;<v1>]!` — set servo direction(s).

    A is 2-axis (pan=v0, tilt=v1); B and C are 1-axis (v1 ignored).
    Values are clamped to {-1, 0, +1}.
    """
    sid = str(servo_id).upper()
    if sid not in SERVO_IDS:
        raise ValueError(f"servo id must be one of {SERVO_IDS}, got {servo_id!r}")
    d0 = _clamp_dir(v0)
    if SERVO_AXES[sid] == 2:
        d1 = _clamp_dir(0 if v1 is None else v1)
        return f"SV;{sid};{d0};{d1}{TERMINATOR}"
    return f"SV;{sid};{d0}{TERMINATOR}"


def servo_stop(servo_id: str) -> str:
    """Stop/hold a single servo (all its axes to 0)."""
    return servo(servo_id, 0, 0)


# ── GNC chassis commands ─────────────────────────────────────────────────────

def gnc_move(direction) -> str:
    """`GNC;move;1!` / `GNC;move;-1!` — drive forward / reverse.

    AppGNC only handles +1 / -1 for move; 0 is not a valid move (use gnc_stop()).
    """
    d = _clamp_dir(direction)
    if d == 0:
        raise ValueError("gnc_move needs +1 or -1; use gnc_stop() to stop")
    return f"GNC;move;{d}{TERMINATOR}"


def gnc_stop() -> str:
    """`GNC;stop!` — stop chassis motion."""
    return f"GNC;stop{TERMINATOR}"


def gnc_update() -> str:
    """`GNC;update!` — request a status reply (AppGNC replies on Serial1)."""
    return f"GNC;update{TERMINATOR}"


# ── Free-text serial prompt ──────────────────────────────────────────────────

def raw(text: str) -> str:
    """Frame arbitrary user-typed text for the serial prompt.

    Appends the terminator only if the user didn't already type one.
    """
    text = text.strip()
    if text.endswith("!"):
        return text
    return text + TERMINATOR
