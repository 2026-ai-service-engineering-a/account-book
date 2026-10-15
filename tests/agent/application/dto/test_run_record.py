from __future__ import annotations

from agent.application.dto import RunRecord, RunSeat


def test_single_shot_seats_count_nothing_yet():
    run = RunRecord("r1", RunSeat.CAPTURE, "카페 5천원", "read")
    assert (run.failed, run.steps, run.tokens, run.cost_usd, run.tool_calls) == (
        False,
        0,
        0,
        0.0,
        (),
    )
