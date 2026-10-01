from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from api.application.dto import BudgetStatus

from .category_body import CategoryBody


class BudgetStatusBody(BaseModel):
    """예산 한 줄. 예산을 정하지 않았으면 limit부터 아래가 전부 null이다."""

    category: CategoryBody
    limit: int | None
    spent: int
    remaining: int | None
    percent: int | None
    projected: int | None
    over_on: date | None

    @classmethod
    def of(cls, status: BudgetStatus) -> BudgetStatusBody:
        return cls(
            category=CategoryBody.of(status.category),
            limit=status.limit.amount if status.limit is not None else None,
            spent=status.spent.amount,
            remaining=status.remaining.amount if status.remaining is not None else None,
            percent=status.percent,
            projected=status.projected.amount if status.projected is not None else None,
            over_on=status.over_on,
        )
