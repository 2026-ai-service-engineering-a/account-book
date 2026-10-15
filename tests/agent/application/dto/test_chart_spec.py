from __future__ import annotations

from agent.application.dto import ChartSpec


def test_a_spec_has_no_values_by_default():
    spec = ChartSpec("bar", "t", "call_1", "name", "spent", "KRW")
    assert not spec.carried_values and spec.annotate == ()
