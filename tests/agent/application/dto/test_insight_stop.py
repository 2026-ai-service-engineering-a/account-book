from __future__ import annotations

from agent.application.dto import InsightStop


def test_the_ways_a_report_run_ends():
    assert {s.value for s in InsightStop} == {
        "assembled",
        "discarded",
        "no_plan",
        "no_base",
        "malformed",
        "wall_clock",
        "cached",
    }


def test_only_answers_that_would_come_out_the_same_are_cached():
    # 장애·시간 초과는 다음에 다시 해 볼 일이다 — 담으면 고쳐진 뒤에도 빈 리포트가 나온다
    assert {s for s in InsightStop if s.cacheable} == {
        InsightStop.ASSEMBLED,
        InsightStop.DISCARDED,
        InsightStop.NO_PLAN,
    }
