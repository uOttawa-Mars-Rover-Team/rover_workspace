"""Strict simulation adapter for the existing arm velocity protocol."""

import math


def velocity_command(frame, scales):
    """Return six scaled velocities; reject unsupported or malformed commands."""
    if len(scales) != 6 or not all(math.isfinite(v) and v > 0 for v in scales):
        raise ValueError("six positive, finite velocity scales are required")
    fields = frame.strip().split(";")
    if fields == ["stop", "!"]:
        return [0.0] * 6
    if len(fields) != 8 or fields[0] != "S" or fields[-1] != "!":
        raise ValueError("expected S;<TW>;<EL>;<SL>;<WP>;<WR>;<EE>;!")
    values = [float(value) for value in fields[1:-1]]
    if not all(math.isfinite(value) for value in values):
        raise ValueError("velocity multipliers must be finite")
    return [max(-1.0, min(1.0, value)) * scale for value, scale in zip(values, scales)]
