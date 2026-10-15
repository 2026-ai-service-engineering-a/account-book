from __future__ import annotations

from agent.application.dto import Chart, ChartPoint


def test_carries_no_colour_or_axis():
    drawn = Chart("hbar", "9월", "KRW", (ChartPoint("식비", 412000),))
    assert not {"color", "axis", "ticks"} & set(Chart.__slots__)
    assert drawn.note == ""
