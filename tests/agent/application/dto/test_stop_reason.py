from __future__ import annotations

from agent.application.dto import StopReason


def test_one_normal_end_and_the_reasons_a_run_is_cut():
    assert StopReason.ANSWERED.value == "answered"
    assert {"max_steps", "max_cost", "wall_clock", "repeated"} <= {r.value for r in StopReason}
