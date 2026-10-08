from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

import pytest

from api.application.dto import Frequency, Totals, TransactionQuery
from api.application.ports import StatsRepository
from api.domain.values import CategoryId, Direction, Money, Period
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


@pytest.mark.parametrize(
    "query",
    [
        TransactionQuery(),
        TransactionQuery(text="스타"),
        TransactionQuery(text="메모만"),
        TransactionQuery(category_id=CategoryId("food"), direction=Direction.EXPENSE),
        TransactionQuery(direction=Direction.INCOME),
        TransactionQuery(start=datetime(2026, 9, 1, 2, tzinfo=UTC)),
    ],
)
def test_frequency_counts_what_the_list_shows(uow, query):
    for n in range(3):
        uow.transactions.add(tx(n))
    uow.transactions.add(tx(10, merchant="스타벅스", category="cafe"))
    uow.transactions.add(tx(11, merchant="편의점", memo="메모만"))
    uow.transactions.add(replace(tx(12, category="salary"), direction=Direction.INCOME))
    listed = uow.transactions.search(replace(query, limit=200)).items
    assert uow.stats.frequency(query).count == len(listed) > 0


def test_frequency_days_are_the_users_days(uow):
    uow.transactions.add(tx(0))  # 서울 9/1 09시
    uow.transactions.add(tx(16))  # 서울 9/2 01시 — UTC로는 아직 9/1
    uow.transactions.add(tx(20))  # 서울 9/2 05시 — 같은 날 두 번째
    uow.transactions.add(tx(64))  # 서울 9/4 01시
    found = uow.stats.frequency(TransactionQuery())
    assert (found.count, found.day_count, found.avg_gap_days) == (4, 3, 1.5)


def test_frequency_rounds_half_away_from_zero(uow):
    uow.transactions.add(tx(0))  # 1000원
    uow.transactions.add(tx(1))  # 1001원 — 평균 1000.5
    assert uow.stats.frequency(TransactionQuery()) == Frequency(2, 1, None, Money(1001))


def test_frequency_of_nothing(uow):
    assert uow.stats.frequency(TransactionQuery()) == Frequency(0, 0, None, None)
