from __future__ import annotations

from datetime import datetime

from api.application.use_cases import CreateTransaction
from api.domain.values import CategoryId, Direction, Money, Period
from tests.api.conftest import SEOUL, FakeUnitOfWork, draft


def ledger() -> FakeUnitOfWork:
    """8월과 9월에 거래가 조금 있는 가계부. 식비 예산은 8월에 30만 원으로 정했다."""
    uow = FakeUnitOfWork()
    create = CreateTransaction(Money(10_000_000))
    for day, amount, category in [
        (5, 10_000, "food"),
        (20, 20_000, "food"),
        (21, 4_000, "cafe"),
    ]:
        create(uow, draft(amount, category, at=_at(8, day)), run_id=None, confirmed=True)
    for day, amount, category in [(1, 100_000, "food"), (2, 80_000, "food"), (3, 5_000, "cafe")]:
        create(uow, draft(amount, category, at=_at(9, day)), run_id=None, confirmed=True)
    create(
        uow,
        draft(3_000_000, "salary", Direction.INCOME, at=_at(9, 10)),
        run_id=None,
        confirmed=True,
    )
    uow.budgets.set_limit(CategoryId("food"), Period(2026, 8), Money(300_000))
    return uow


def _at(month: int, day: int) -> datetime:
    return datetime(2026, month, day, 12, tzinfo=SEOUL)
