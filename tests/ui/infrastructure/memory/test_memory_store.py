from __future__ import annotations

from tests.ui.conftest import draft
from ui.application.dto import Direction, Period, Source, Transaction, TransactionFilter


def put(store, merchant, day, category="food", memo=""):
    base = draft(day=day, category=category, merchant=merchant)
    tx = Transaction(
        store.next_id(),
        base.direction,
        base.amount,
        base.occurred_at,
        base.category_id,
        "card",
        merchant,
        memo,
        Source.MANUAL,
    )
    store.transactions[tx.id] = tx
    return tx


def test_ids_are_sequential(store):
    assert (store.next_id(), store.next_id()) == ("t00001", "t00002")


def test_matching_combines_conditions(store):
    put(store, "스타벅스 강남", 3, "cafe")
    put(store, "김밥천국", 4, memo="스타 모임")
    put(store, "스타벅스", 5, "cafe")
    criteria = TransactionFilter(Period(2026, 9), Direction.EXPENSE, "cafe", "스타")
    assert sorted(t.merchant for t in store.matching(criteria)) == ["스타벅스", "스타벅스 강남"]
    memo_hit = store.matching(TransactionFilter(Period(2026, 9), query="모임"))
    assert [t.merchant for t in memo_hit] == ["김밥천국"]
    assert store.matching(TransactionFilter(Period(2026, 8))) == []


def test_validate_all_fields(store):
    assert store.validate(draft()) == {}
    bad = draft(amount=0, category="nope")
    assert set(store.validate(bad)) == {"amount", "category_id"}
    assert "amount" in store.validate(draft(amount=10_000_000_001))


def test_clear_keeps_catalog(store):
    put(store, "x", 1)
    store.limits["food"] = 1
    store.clear()
    assert (store.transactions, store.limits, store.replies) == ({}, {}, {})
    assert "food" in store.categories
