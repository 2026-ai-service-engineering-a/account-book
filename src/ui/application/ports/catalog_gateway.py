from __future__ import annotations

from typing import Protocol

from ui.application.dto import Account, Category, Direction


class CatalogGateway(Protocol):
    """카테고리와 결제수단 목록. 둘 다 api가 가진 기준 데이터다."""

    async def categories(self, direction: Direction | None = None) -> tuple[Category, ...]: ...

    async def accounts(self) -> tuple[Account, ...]: ...
