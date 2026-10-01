from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import insert

from api.application.ports import CategoryIndex
from api.domain.entities import Transaction
from api.domain.rules.searchable_text import text_hash
from api.domain.values import AccountId, CategoryId, Direction, Money, Source, TransactionId
from api.infrastructure.db.reference_seeder import seed_reference
from api.infrastructure.db.rows import CategoryRuleRow
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration
MODEL = "m@768"
EXPENSE = {CategoryId(c) for c in ("food", "cafe", "living")}


def unit(*hot: int) -> tuple[float, ...]:
    return tuple(1.0 if i in hot else 0.0 for i in range(768))


def tx(n: int, merchant: str, category: str = "food", hours: int = 0) -> Transaction:
    return Transaction(
        id=TransactionId(f"t{n:03d}"),
        direction=Direction.EXPENSE,
        amount=Money(1000),
        occurred_at=datetime(2026, 9, 1, tzinfo=UTC) + timedelta(hours=hours or n),
        category_id=CategoryId(category),
        account_id=AccountId("card"),
        merchant=merchant,
        memo="",
        source=Source.MANUAL,
    )


@pytest.fixture
def uow(migrated):
    with migrated.begin() as connection:
        seed_reference(connection)
    with SqlUnitOfWork(SqlUnitOfWork.factory(migrated)) as work:
        yield work


def test_writes_carry_the_searchable_text(uow):
    uow.transactions.add(tx(1, "김밥천국 강남점"))
    port: CategoryIndex = uow.index
    (only,) = port.pending(MODEL, 10)
    assert only.text == "김밥천국" and only.text_hash == text_hash("김밥천국")


def test_rule_longest_pattern_wins(uow):
    uow.transactions.add(tx(1, "x"))
    uow._session.execute(
        insert(CategoryRuleRow),
        [
            {"merchant_pattern": "김밥", "category_id": "cafe", "source": "user"},
            {"merchant_pattern": "김밥천국", "category_id": "food", "source": "user"},
        ],
    )
    assert uow.index.rule_match("김밥천국 점심", EXPENSE) == "food"
    assert uow.index.rule_match("스타벅스", EXPENSE) is None


def test_history_newest_first(uow):
    for n in range(6):
        uow.transactions.add(tx(n, "김밥천국"))
    recent = uow.index.recent_with_text(text_hash("김밥천국"), Direction.EXPENSE, 5)
    assert [e.transaction_id for e in recent] == ["t005", "t004", "t003", "t002", "t001"]


def test_nearest_by_cosine_one_neighbour_per_text_and_category(uow):
    uow.transactions.add(tx(1, "스타벅스", "cafe", hours=1))
    uow.transactions.add(tx(2, "스타벅스", "cafe", hours=9))  # 같은 텍스트 — 대표는 최근 것
    uow.transactions.add(tx(3, "김밥천국", "food"))
    uow.transactions.add(tx(4, "이마트", "living"))
    for text, vector in [("스타벅스", unit(0)), ("김밥천국", unit(1)), ("이마트", unit(2))]:
        uow.index.put_embedding(MODEL, text_hash(text), vector)
    near = uow.index.nearest(MODEL, unit(0, 1), Direction.EXPENSE, EXPENSE, limit=2)
    assert [e.merchant for e in near] == ["스타벅스", "김밥천국"] or [e.merchant for e in near] == [
        "김밥천국",
        "스타벅스",
    ]
    starbucks = next(e for e in near if e.merchant == "스타벅스")
    assert starbucks.transaction_id == "t002" and starbucks.similarity == pytest.approx(
        0.7071, 1e-3
    )
    assert len(near) == 2


def test_embedding_round_trip_and_pending(uow):
    uow.transactions.add(tx(1, "스타벅스"))
    assert uow.index.stored_vector(MODEL, text_hash("스타벅스")) is None
    uow.index.put_embedding(MODEL, text_hash("스타벅스"), unit(3))
    uow.index.put_embedding(MODEL, text_hash("스타벅스"), unit(4))  # 같은 열쇠는 덮는다
    assert uow.index.stored_vector(MODEL, text_hash("스타벅스")) == unit(4)
    assert uow.index.pending(MODEL, 10) == ()
    assert len(uow.index.pending("other@768", 10)) == 1  # 모델이 바뀌면 다시 색인할 것
