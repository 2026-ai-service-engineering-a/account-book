from __future__ import annotations

from ui.application.dto import MonthTotal, Period
from ui.application.values import Money
from ui.interfaces.charts.month_bar_chart import MonthBarChart


def test_groups_share_one_axis():
    chart = MonthBarChart.build(
        [
            MonthTotal(Period(2026, 8), Money(1_215_000), Money(3_200_000)),
            MonthTotal(Period(2026, 9), Money(0), Money(0)),
        ]
    )
    assert [g["label"] for g in chart.groups] == ["8월", "9월"]
    assert chart.grid[0]["label"] == "0" and chart.grid[-1]["label"] == "400만"
    assert chart.groups[0]["income_title"] == "8월 수입 3,200,000원"
