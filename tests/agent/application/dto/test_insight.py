from __future__ import annotations

from agent.application.dto import Insight, InsightStop


def test_a_quiet_month_is_an_empty_insight():
    quiet = Insight(InsightStop.NO_PLAN)
    assert quiet.charts == () and quiet.highlights == () and quiet.whys == {}
