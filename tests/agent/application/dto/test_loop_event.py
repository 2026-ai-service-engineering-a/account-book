from __future__ import annotations

import pytest

from agent.application.dto import LoopEvent, LoopOutcome, ModelUsage, StopReason

DONE = LoopOutcome(StopReason.ANSWERED, "끝", (), ModelUsage(), 1)


def test_a_tool_name_or_the_end():
    assert LoopEvent(tool="count_frequency").outcome is None
    assert LoopEvent(outcome=DONE).tool == ""


@pytest.mark.parametrize("build", [lambda: LoopEvent(), lambda: LoopEvent("x", DONE)])
def test_never_both_never_neither(build):
    with pytest.raises(ValueError):
        build()
