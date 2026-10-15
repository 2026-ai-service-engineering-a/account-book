from __future__ import annotations

from agent.application.dto import InsightStop


def test_the_ways_a_report_run_ends():
    assert {s.value for s in InsightStop} == {
        "assembled",
        "discarded",
        "no_plan",
        "no_base",
        "malformed",
    }
