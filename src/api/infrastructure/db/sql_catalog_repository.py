from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.domain.entities import Account, Category
from api.domain.values import AccountId, CategoryId, Direction

from .rows import AccountRow, CategoryRow


class SqlCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def categories(self, direction: Direction | None = None) -> tuple[Category, ...]:
        statement = select(CategoryRow).order_by(CategoryRow.position, CategoryRow.id)
        if direction is not None:
            statement = statement.where(CategoryRow.direction == direction.value)
        return tuple(
            Category(CategoryId(r.id), r.name, Direction(r.direction))
            for r in self._session.scalars(statement)
        )

    def accounts(self) -> tuple[Account, ...]:
        statement = select(AccountRow).order_by(AccountRow.position, AccountRow.id)
        return tuple(
            Account(AccountId(r.id), r.name, r.kind) for r in self._session.scalars(statement)
        )
