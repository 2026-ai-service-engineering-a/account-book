from __future__ import annotations

from datetime import date

from ui.application.dto import Category, Direction, PaceSeries
from ui.interfaces.charts.pace_chart import PaceChart

FOOD = Category("food", "식비", Direction.EXPENSE)


def series(cumulative, over_on=None, projected=321_705):
    return PaceSeries(FOOD, 300_000, tuple(cumulative), 30, projected, over_on)


def test_projection_reaches_month_end():
    chart = PaceChart.build(series([10_000 * d for d in range(1, 18)], date(2026, 9, 28)))
    assert chart.title == "식비 — 이 페이스면 예산을 넘는다"
    assert chart.projection is not None and chart.projection.endswith(
        " 600.0," + str(chart.projection.split(",")[-1])
    )
    assert chart.over_x is not None and chart.over_title == "9/28 예산 초과"
    assert [t["label"] for t in chart.ticks] == ["1일", "10일", "17일", "20일", "30일"]


def test_finished_month_has_no_projection():
    chart = PaceChart.build(series([5_000 * d for d in range(1, 31)], projected=150_000))
    assert chart.projection is None
    assert chart.title == "식비 — 이 페이스면 예산 안이다"


def test_crowded_ticks_are_dropped():
    chart = PaceChart.build(series([1_000] * 11))
    assert "10일" not in [t["label"] for t in chart.ticks]
