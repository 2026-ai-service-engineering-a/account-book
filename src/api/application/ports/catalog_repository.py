from __future__ import annotations

from typing import Protocol

from api.domain.entities import Account, Category
from api.domain.values import Direction


class CatalogRepository(Protocol):
    """카테고리와 결제수단 — 기준 데이터."""

    def categories(self, direction: Direction | None = None) -> tuple[Category, ...]: ...

    def accounts(self) -> tuple[Account, ...]: ...
