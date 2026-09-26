from __future__ import annotations

from ui.application.dto import Account, Category, Direction

from .memory_store import MemoryStore


class MemoryCatalogGateway:
    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    async def categories(self, direction: Direction | None = None) -> tuple[Category, ...]:
        return tuple(
            c
            for c in self._store.categories.values()
            if direction is None or c.direction == direction
        )

    async def accounts(self) -> tuple[Account, ...]:
        return tuple(self._store.accounts.values())
