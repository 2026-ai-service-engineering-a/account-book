from __future__ import annotations

from agent.domain.tools import ComparePeriodsInput
from agent.domain.values import PeriodName, PeriodSpec


def test_two_periods_and_an_optional_category():
    last, this = PeriodSpec(PeriodName.LAST_MONTH), PeriodSpec(PeriodName.THIS_MONTH)
    found = ComparePeriodsInput(last, this)
    assert found.category_id is None
