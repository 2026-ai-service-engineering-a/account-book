from __future__ import annotations

from ui.application.values import Money
from ui.interfaces.charts.category_bar_chart import CategoryBarChart


def test_largest_bar_takes_full_width():
    chart = CategoryBarChart.build([("주거", Money(450_000)), ("카페", Money(31_000))])
    assert chart.height == 72
    first, second = chart.bars
    assert first["value_x"] == 462.0  # 54 + 400 + 8
    assert first["title"] == "주거 450,000원"
    assert second["text_y"] == 49


def test_tiny_bar_is_square():
    (bar,) = CategoryBarChart.build([("x", Money(0))]).bars
    assert "A4" not in bar["path"]
