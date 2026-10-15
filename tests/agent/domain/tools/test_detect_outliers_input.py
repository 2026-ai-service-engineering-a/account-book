from __future__ import annotations

from agent.domain.tools import DetectOutliersInput
from agent.domain.values import Direction, PeriodName, PeriodSpec


def test_spending_by_default_and_no_threshold_to_pass():
    found = DetectOutliersInput(PeriodSpec(PeriodName.LAST_MONTH))
    assert found.direction is Direction.EXPENSE
    assert not hasattr(found, "threshold")
