from __future__ import annotations

from agent.application.dto import InsightState, InsightStop


def test_end_freezes_what_was_gathered():
    state = InsightState(model_calls=2, replanned=True)
    state.whys["call_3"] = "큰 건"
    ended = state.end(InsightStop.ASSEMBLED)
    state.whys["call_4"] = "나중"
    assert ended.whys == {"call_3": "큰 건"} and ended.model_calls == 2 and ended.replanned
