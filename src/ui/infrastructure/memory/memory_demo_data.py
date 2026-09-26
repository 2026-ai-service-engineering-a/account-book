from __future__ import annotations

from ui.application.ports import Clock

from .demo_seed import seed_demo
from .memory_store import MemoryStore


class MemoryDemoData:
    def __init__(self, store: MemoryStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    async def reset(self, filled: bool) -> None:
        self._store.clear()
        if filled:
            seed_demo(self._store, self._clock.now())
