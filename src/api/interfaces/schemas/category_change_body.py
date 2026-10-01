from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import CategoryChange

from .category_body import CategoryBody


class CategoryChangeBody(BaseModel):
    category: CategoryBody
    this_month: int
    last_month: int | None
    delta: int | None
    percent: int | None

    @classmethod
    def of(cls, change: CategoryChange) -> CategoryChangeBody:
        return cls(
            category=CategoryBody.of(change.category),
            this_month=change.this_month.amount,
            last_month=change.last_month.amount if change.last_month is not None else None,
            delta=change.delta.amount if change.delta is not None else None,
            percent=change.percent,
        )
