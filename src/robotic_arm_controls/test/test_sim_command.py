"""Check malformed input cannot become a moving simulation command."""

import pytest

from robotic_arm_controls.sim_command import velocity_command


def test_channel_order_and_scaling():
    assert velocity_command("S;1;0.5;0;-0.5;-1;2;!", [1, 2, 3, 4, 5, 6]) == [1, 1, 0, -2, -5, 6]


@pytest.mark.parametrize("frame", [
    "S;1;2;!", "S;1;2;3;4;5;6", "S;1;2;3;4;5;nan;!",
    "S;1;2;3;4;5;inf;!", "set0;!", "S;1;2;3;4;5;x;!",
])
def test_invalid_commands_are_rejected(frame):
    with pytest.raises(ValueError):
        velocity_command(frame, [0.25] * 6)


def test_stop():
    assert velocity_command("stop;!", [0.25] * 6) == [0] * 6
