from __future__ import annotations

import asyncio

from ui.infrastructure.memory import MemoryDemoData


def test_reset_empty_then_filled(store, clock):
    demo = MemoryDemoData(store, clock)
    asyncio.run(demo.reset(filled=True))
    assert store.transactions and store.limits
    asyncio.run(demo.reset(filled=False))
    assert not store.transactions and not store.limits
