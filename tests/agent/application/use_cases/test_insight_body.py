from __future__ import annotations

from agent.application.dto import Chart, ChartPoint, Insight, InsightStop
from agent.application.use_cases.insight_body import insight_body, insight_from_body

DRAWN = Chart("hbar", "9월", "KRW", (ChartPoint("생활", 1050000, True),), "")


def test_what_goes_to_the_screen_comes_back_as_cached():
    body = insight_body(Insight(InsightStop.ASSEMBLED, (DRAWN,), ("생활이 늘었어요.",)))
    back = insight_from_body(body)
    assert back is not None and back.stop is InsightStop.CACHED
    assert back.charts == (DRAWN,) and back.highlights == ("생활이 늘었어요.",)
    assert "steps" not in body and "whys" not in body  # 감사 로그의 몫은 담지 않는다


def test_a_body_of_the_wrong_shape_is_none():
    bad_points = {"charts": [{"kind": "bar", "points": [["a", "?", False]]}], "highlights": []}
    for body in ({}, {"charts": [], "highlights": [1]}, bad_points):
        assert insight_from_body(body) is None
