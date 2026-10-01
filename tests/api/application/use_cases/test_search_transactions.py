from __future__ import annotations

from datetime import UTC, datetime

from api.application.use_cases import SearchTransactions
from api.domain.values import Period
from tests.api.conftest import SEOUL, FakeUnitOfWork


def test_period_becomes_utc_bounds_in_the_users_zone():
    uow = FakeUnitOfWork()
    SearchTransactions(uow, SEOUL)(period=Period(2026, 9), text="  김밥 ")
    query = uow.transactions.last_query
    assert query.start == datetime(2026, 8, 31, 15, tzinfo=UTC)
    assert query.end == datetime(2026, 9, 30, 15, tzinfo=UTC)
    assert query.text == "김밥"


def test_no_period_means_no_bounds_and_limit_is_capped():
    uow = FakeUnitOfWork()
    SearchTransactions(uow, SEOUL)(limit=10_000)
    query = uow.transactions.last_query
    assert query.start is None and query.limit == 200
