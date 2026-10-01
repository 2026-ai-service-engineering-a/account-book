from __future__ import annotations

import pytest

from api.application.ports import BudgetRepository
from api.domain.values import CategoryId, Money, Period
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration
FOOD = CategoryId("food")


def test_carries_forward_until_changed_or_cleared(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    with SqlUnitOfWork(SqlUnitOfWork.factory(migrated)) as uow:
        port: BudgetRepository = uow.budgets
        port.set_limit(FOOD, Period(2026, 5), Money(300_000))
        port.set_limit(FOOD, Period(2026, 8), Money(250_000))
        port.set_limit(FOOD, Period(2026, 10), None)
        assert port.limits(Period(2026, 4)) == {}
        assert port.limits(Period(2026, 7)) == {FOOD: Money(300_000)}
        assert port.limits(Period(2026, 9)) == {FOOD: Money(250_000)}
        assert port.limits(Period(2026, 11)) == {}  # 10월부터 예산 없음
        port.set_limit(FOOD, Period(2026, 8), Money(200_000))  # 같은 달은 덮는다
        assert port.limits(Period(2026, 8)) == {FOOD: Money(200_000)}
