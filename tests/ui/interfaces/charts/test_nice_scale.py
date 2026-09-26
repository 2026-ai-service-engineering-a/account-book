from __future__ import annotations

from ui.interfaces.charts.nice_scale import axis_label, nice_step, scale_top


def test_steps_are_round_numbers():
    assert nice_step(321_705) == 200_000
    assert nice_step(3_200_000) == 2_000_000
    assert nice_step(0) == 1


def test_scale_top_covers_peak():
    assert scale_top(321_705, 200_000) == 400_000
    assert scale_top(0, 1) == 1


def test_axis_label_uses_man():
    assert axis_label(0) == "0"
    assert axis_label(100_000) == "10만"
    assert axis_label(2_000_000) == "200만"
    assert axis_label(1_500) == "1,500"
