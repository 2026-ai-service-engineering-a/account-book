from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine

from api.application.dto import TransactionQuery
from api.application.ports import TransactionRepository
from api.domain.entities import Transaction
from api.domain.values import AccountId, CategoryId, Direction, Money, Source, TransactionId
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration
BASE = datetime(2026, 9, 1, tzinfo=UTC)


def tx(n: int, merchant: str = "김밥천국", category: str = "food", memo: str = "") -> Transaction:
    return Transaction(
        id=TransactionId(f"t{n:03d}"),
        direction=Direction.EXPENSE,
        amount=Money(1000 + n),
        occurred_at=BASE + timedelta(hours=n),
        category_id=CategoryId(category),
        account_id=AccountId("card"),
        merchant=merchant,
        memo=memo,
        source=Source.MANUAL,
    )


@pytest.fixture
def uow(migrated: Engine):
    with migrated.begin() as connection:
        seed_reference(connection)
    work = SqlUnitOfWork(SqlUnitOfWork.factory(migrated))
    with work:
        yield work


def test_fills_the_port(uow):
    port: TransactionRepository = uow.transactions
    assert port is not None


def test_add_get_replace_remove(uow):
    uow.transactions.add(tx(1))
    assert uow.transactions.get(TransactionId("t001")) == tx(1)
    uow.transactions.replace(tx(1, merchant="김가네"))
    assert uow.transactions.get(TransactionId("t001")).merchant == "김가네"
    uow.transactions.remove(TransactionId("t001"))
    assert uow.transactions.get(TransactionId("t001")) is None


def test_pages_newest_first_without_overlap(uow):
    for n in range(5):
        uow.transactions.add(tx(n))
    first = uow.transactions.search(TransactionQuery(limit=2))
    second = uow.transactions.search(TransactionQuery(limit=2, cursor=first.next_cursor))
    third = uow.transactions.search(TransactionQuery(limit=2, cursor=second.next_cursor))
    ids = [t.id for page in (first, second, third) for t in page.items]
    assert ids == ["t004", "t003", "t002", "t001", "t000"] and third.next_cursor is None


def test_filters(uow):
    uow.transactions.add(tx(1))
    uow.transactions.add(tx(2, merchant="스타벅스", category="cafe"))
    uow.transactions.add(tx(30, memo="100% 환불"))
    search = uow.transactions.search
    assert [t.id for t in search(TransactionQuery(category_id=CategoryId("cafe"))).items] == [
        "t002"
    ]
    assert [t.id for t in search(TransactionQuery(text="스타")).items] == ["t002"]
    assert [t.id for t in search(TransactionQuery(text="100%")).items] == ["t030"]
    window = TransactionQuery(start=BASE + timedelta(hours=2), end=BASE + timedelta(hours=30))
    assert [t.id for t in search(window).items] == ["t002"]  # 끝은 열린 구간
