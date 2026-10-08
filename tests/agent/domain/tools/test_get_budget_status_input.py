from __future__ import annotations

from datetime import date

import pytest

from agent.domain.tools import GetBudgetStatusInput
from agent.domain.values import PeriodName, PeriodSpec


def test_months_only():
    GetBudgetStatusInput(PeriodSpec(PeriodName.THIS_MONTH))
    GetBudgetStatusInput(PeriodSpec(PeriodName.MONTH, start=date(2026, 8, 1)))
    with pytest.raises(ValueError, match="달 단위"):
        GetBudgetStatusInput(PeriodSpec(PeriodName.THIS_WEEK))
