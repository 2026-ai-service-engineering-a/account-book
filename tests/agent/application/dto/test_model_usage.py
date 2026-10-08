from __future__ import annotations

from agent.application.dto import ModelUsage


def test_adds_up_across_steps():
    total = ModelUsage(100, 20, 0.001) + ModelUsage(50, 10, 0.002)
    assert (total.input_tokens, total.output_tokens) == (150, 30)
    assert round(total.cost_usd, 6) == 0.003
    assert ModelUsage() == ModelUsage(0, 0, 0.0)
