from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import PeriodChange

from .category_body import CategoryBody


class PeriodChangeBody(BaseModel):
    """두 기간 비교의 한 줄. `delta`는 b - a, `percent`는 a 대비 절댓값이고 a가 0이면 null."""

    category: CategoryBody
    a: int
    b: int
    delta: int
    percent: int | None

    @classmethod
    def of(cls, change: PeriodChange) -> PeriodChangeBody:
        return cls(
            category=CategoryBody.of(change.category),
            a=change.a.amount,
            b=change.b.amount,
            delta=change.delta.amount,
            percent=change.percent,
        )
