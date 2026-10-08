from __future__ import annotations

from agent.application.dto import LoopOutcome, ModelUsage, StopReason


def test_a_cut_run_still_has_an_outcome():
    outcome = LoopOutcome(StopReason.MAX_STEPS, "", (), ModelUsage(), 8)
    assert outcome.text == "" and outcome.model_calls == 8
