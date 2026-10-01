from __future__ import annotations

from collections.abc import Callable

from api.application.ports import UnitOfWork
from api.domain.entities import Account, Category
from api.domain.values import Direction


class ListCatalog:
    """카테고리와 결제수단 목록 — 화면의 셀렉트가 쓴다."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def categories(self, direction: Direction | None = None) -> tuple[Category, ...]:
        with self._unit_of_work() as uow:
            return uow.catalog.categories(direction)

    def accounts(self) -> tuple[Account, ...]:
        with self._unit_of_work() as uow:
            return uow.catalog.accounts()
