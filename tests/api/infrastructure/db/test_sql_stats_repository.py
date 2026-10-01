from __future__ import annotations

from datetime import UTC, datetime

import pytest

from api.application.dto import Totals, TransactionQuery
from api.application.ports import StatsRepository
from api.domain.values import CategoryId, Money, Period
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from tests.api.conftest import SEOUL
from tests.api.infrastructure.db.test_sql_transaction_repository import tx

pytestmark = pytest.mark.integration


@pytest.fixture
def uow(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    with SqlUnitOfWork(SqlUnitOfWork.factory(migrated), "Asia/Seoul") as work:
        yield work


def test_totals_with_the_same_filter_as_the_list(uow):
    port: StatsRepository = uow.stats
    for n in range(3):
        uow.transactions.add(tx(n))
    uow.transactions.add(tx(10, merchant="스타벅스", category="cafe"))
    assert port.totals(TransactionQuery()) == Totals(Money(4013), Money(0))
    assert port.totals(TransactionQuery(text="스타")) == Totals(Money(1010), Money(0))


def test_spent_by_category(uow):
    uow.transactions.add(tx(1))
    uow.transactions.add(tx(2))
    uow.transactions.add(tx(3, category="cafe"))
    start, end = Period(2026, 9).bounds(SEOUL)
    assert uow.stats.spent_by_category(start, end) == {
        CategoryId("food"): Money(2003),
        CategoryId("cafe"): Money(1003),
    }


def test_daily_spent_counts_the_day_in_the_users_zone(uow):
    # 9월 1일 00시 UTC는 서울로 9월 1일 09시다. 9월 1일 16시 UTC는 서울로 9월 2일 01시다.
    uow.transactions.add(tx(0))  # 2026-09-01T00:00Z
    uow.transactions.add(tx(16))  # 2026-09-01T16:00Z
    start, end = Period(2026, 9).bounds(SEOUL)
    days = uow.stats.daily_spent(CategoryId("food"), start, end)
    assert days == [(1, Money(1000)), (2, Money(1016))]


def test_first_occurred_at(uow):
    assert uow.stats.first_occurred_at() is None
    uow.transactions.add(tx(5))
    uow.transactions.add(tx(1))
    assert uow.stats.first_occurred_at() == datetime(2026, 9, 1, 1, tzinfo=UTC)
