from __future__ import annotations

from datetime import datetime

import pytest

from api.application.use_cases import ReadBudgetStatuses, SetBudget
from api.domain.errors import ConfirmationRequired, InvalidTransaction
from api.domain.values import CategoryId, Money, Period
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL, FixedClock

CLOCK = FixedClock(datetime(2026, 9, 17, tzinfo=SEOUL))


def test_from_this_month_on_and_returns_the_new_status():
    uow = ledger()
    status = SetBudget(CLOCK)(uow, CategoryId("cafe"), Money(50_000), confirmed=True)
    assert status.limit == Money(50_000) and status.spent == Money(5_000)
    (august,) = ReadBudgetStatuses(uow, CLOCK)(Period(2026, 8), CategoryId("cafe"))
    assert august.limit is None  # 지난달은 그대로


def test_none_means_no_budget_from_this_month_even_if_an_earlier_one_carries():
    uow = ledger()
    status = SetBudget(CLOCK)(uow, CategoryId("food"), None, confirmed=True)
    assert status.limit is None
    (august,) = ReadBudgetStatuses(uow, CLOCK)(Period(2026, 8), CategoryId("food"))
    assert august.limit == Money(300_000)


def test_always_needs_a_confirmation_but_checks_values_first():
    with pytest.raises(ConfirmationRequired):
        SetBudget(CLOCK)(ledger(), CategoryId("cafe"), Money(1), confirmed=False)
    with pytest.raises(InvalidTransaction) as caught:
        SetBudget(CLOCK)(ledger(), CategoryId("salary"), Money(1), confirmed=False)
    assert caught.value.details == {"category_id": "지출 카테고리가 아닙니다."}
    with pytest.raises(InvalidTransaction) as caught:
        SetBudget(CLOCK)(ledger(), CategoryId("cafe"), Money(0), confirmed=False)
    assert caught.value.details == {"amount": "예산은 0보다 커야 합니다."}
