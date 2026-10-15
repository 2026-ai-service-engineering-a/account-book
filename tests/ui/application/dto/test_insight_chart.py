from __future__ import annotations

from ui.application.dto import InsightChart, InsightPoint


def test_a_chart_has_no_colour_or_axis_to_choose():
    chart = InsightChart("hbar", "9월", "KRW", (InsightPoint("식비", 412000),))
    assert chart.note == "" and not {"color", "axis"} & set(InsightChart.__slots__)
