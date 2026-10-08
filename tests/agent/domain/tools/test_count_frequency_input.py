from __future__ import annotations

from agent.domain.tools import CountFrequencyInput
from agent.domain.values import Direction, PeriodName, PeriodSpec


def test_counts_expenses_unless_told():
    assert CountFrequencyInput(PeriodSpec(PeriodName.LAST_WEEK)).direction is Direction.EXPENSE
