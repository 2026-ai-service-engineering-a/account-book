from __future__ import annotations

import asyncio

import pytest

from tests.ui.conftest import draft
from ui.application.dto import Direction, Period, Source, TransactionFilter
from ui.application.errors import LedgerValidationError, TransactionNotFound
from ui.infrastructure.memory import MemoryTransactionGateway


def test_same_idempotency_key_creates_once(store):
    gateway = MemoryTransactionGateway(store)
    first = asyncio.run(gateway.create(draft(), "k1"))
    again = asyncio.run(gateway.create(draft(), "k1"))
    assert first == again
    assert len(store.transactions) == 1


def test_run_id_marks_agent_source(store):
    gateway = MemoryTransactionGateway(store)
    assert asyncio.run(gateway.create(draft(), "k1")).source == Source.MANUAL
    assert asyncio.run(gateway.create(draft(), "k2", run_id="r1")).source == Source.AGENT


def test_validation_reports_each_field(store):
    gateway = MemoryTransactionGateway(store)
    bad = draft(amount=-500, category="salary")
    with pytest.raises(LedgerValidationError) as caught:
        asyncio.run(gateway.create(bad, "k1"))
    assert set(caught.value.details) == {"amount", "category_id"}


def test_search_filters_and_pages(store):
    gateway = MemoryTransactionGateway(store)
    for day in range(1, 6):
        asyncio.run(gateway.create(draft(day=day), f"k{day}"))
    asyncio.run(gateway.create(draft(day=3, category="cafe", merchant="스타벅스"), "c"))
    criteria = TransactionFilter(Period(2026, 9), Direction.EXPENSE, "food")
    page = asyncio.run(gateway.search(criteria, limit=3))
    assert [t.occurred_at.day for t in page.items] == [5, 4, 3]
    rest = asyncio.run(gateway.search(criteria, cursor=page.next_cursor, limit=3))
    assert [t.occurred_at.day for t in rest.items] == [2, 1]
    assert rest.next_cursor is None
    by_name = asyncio.run(gateway.search(TransactionFilter(Period(2026, 9), query="스타")))
    assert [t.merchant for t in by_name.items] == ["스타벅스"]


def test_update_keeps_source_and_delete_removes(store):
    gateway = MemoryTransactionGateway(store)
    created = asyncio.run(gateway.create(draft(), "k1", run_id="r1"))
    updated = asyncio.run(gateway.update(created.id, draft(amount=9_000), "k2"))
    assert (updated.amount, updated.source) == (9_000, Source.AGENT)
    asyncio.run(gateway.delete(created.id, "k3"))
    asyncio.run(gateway.delete(created.id, "k3"))  # 같은 키로 다시 와도 404가 아니다
    with pytest.raises(TransactionNotFound):
        asyncio.run(gateway.get(created.id))
