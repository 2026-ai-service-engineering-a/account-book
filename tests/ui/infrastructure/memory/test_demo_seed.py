from __future__ import annotations

from tests.ui.conftest import NOW
from ui.application.dto import Period
from ui.application.values import CategoryId, Money
from ui.infrastructure.memory.demo_seed import seed_demo


def test_seed_covers_six_months_up_to_now(store):
    seed_demo(store, NOW)
    days = {store.local_day(t) for t in store.transactions.values()}
    assert Period.of(min(days)) == Period(2026, 4)
    assert max(t.occurred_at for t in store.transactions.values()) <= NOW
    assert store.limits[CategoryId("food")] == Money(300_000)


def test_seed_is_deterministic(store):
    seed_demo(store, NOW)
    first = sorted((t.occurred_at, t.amount) for t in store.transactions.values())
    store.clear()
    seed_demo(store, NOW)
    assert sorted((t.occurred_at, t.amount) for t in store.transactions.values()) == first
