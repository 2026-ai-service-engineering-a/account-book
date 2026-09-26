from __future__ import annotations

import asyncio

from ui.application.dto import Direction
from ui.infrastructure.memory import MemoryCatalogGateway


def test_categories_follow_direction(store):
    catalog = MemoryCatalogGateway(store)
    income = asyncio.run(catalog.categories(Direction.INCOME))
    assert {c.name for c in income} == {"급여", "기타수입"}
    assert len(asyncio.run(catalog.categories())) == len(store.categories)


def test_accounts(store):
    names = [a.name for a in asyncio.run(MemoryCatalogGateway(store).accounts())]
    assert names == ["카드", "현금", "계좌이체"]
