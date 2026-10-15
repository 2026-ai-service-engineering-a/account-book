from __future__ import annotations

import pytest

from ui.application.dto import InsightChart, InsightPoint
from ui.interfaces.charts.insight_chart_view import InsightChartView

CHANGES = (InsightPoint("생활", 890000, True), InsightPoint("식비", -12000))


def test_horizontal_bars_grow_both_ways_from_the_zero_line():
    view = InsightChartView.build(InsightChart("hbar", "달라진 것", "KRW", CHANGES))
    rise, fall = view.marks
    assert rise["x"] == pytest.approx(view.zero) and rise["w"] > fall["w"]
    assert fall["x"] + fall["w"] == pytest.approx(view.zero)  # 음수는 0선의 왼쪽
    assert rise["value"] == "890,000원" and fall["value"] == ""  # 숫자는 표시한 점에만
    assert fall["title"] == "식비 -12,000원"  # 정확한 값은 마우스를 올리면


def test_columns_and_lines_share_the_zero_line_and_format_by_unit():
    days = (InsightPoint("8월", 1.4, True), InsightPoint("9월", 2.0, True))
    bars = InsightChartView.build(InsightChart("bar", "간격", "days", days))
    assert [m["value"] for m in bars.marks] == ["1.4일", "2일"] and bars.line == ""
    counts = (InsightPoint("8월", 3), InsightPoint("9월", 7, True))
    line = InsightChartView.build(InsightChart("line", "횟수", "count", counts))
    assert len(line.line.split()) == 2 and line.marks[1]["value"] == "7건"
