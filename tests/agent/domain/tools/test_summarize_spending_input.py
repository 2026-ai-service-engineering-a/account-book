from __future__ import annotations

from agent.domain.tools import SummarizeSpendingInput
from agent.domain.values import PeriodName, PeriodSpec


def test_only_the_period_is_needed():
    found = SummarizeSpendingInput(PeriodSpec(PeriodName.THIS_MONTH))
    assert (found.category_id, found.merchant, found.direction) == (None, "", None)
