from __future__ import annotations

from datetime import date, datetime

from api.application.use_cases import ReadBudgetStatuses
from api.domain.values import CategoryId, Money, Period
from tests.api.application.use_cases.conftest import ledger
from tests.api.conftest import SEOUL, FixedClock

CLOCK = FixedClock(datetime(2026, 9, 3, 18, tzinfo=SEOUL))


def test_budget_carries_forward_and_paces():
    statuses = {s.category.id: s for s in ReadBudgetStatuses(ledger(), CLOCK)(Period(2026, 9))}
    food = statuses[CategoryId("food")]
    # 8월에 정한 예산이 9월에도 이어진다
    assert food.limit == Money(300_000) and food.spent == Money(180_000)
    assert food.remaining == Money(120_000) and food.percent == 60
    assert food.projected == Money(1_800_000)  # 사흘에 18만 원 → 30일이면
    assert food.over_on == date(2026, 9, 6)
    assert statuses[CategoryId("cafe")].limit is None  # 정하지 않은 것도 들어 있다


def test_one_category():
    (only,) = ReadBudgetStatuses(ledger(), CLOCK)(Period(2026, 9), CategoryId("cafe"))
    assert only.spent == Money(5_000)
