from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from api.application.dto import PaceSeries

from .category_body import CategoryBody


class PaceBody(BaseModel):
    category: CategoryBody
    limit: int
    cumulative: list[int]  # 1일부터 오늘(또는 말일)까지의 누적
    days_in_month: int
    projected: int
    over_on: date | None

    @classmethod
    def of(cls, pace: PaceSeries) -> PaceBody:
        return cls(
            category=CategoryBody.of(pace.category),
            limit=pace.limit.amount,
            cumulative=[m.amount for m in pace.cumulative],
            days_in_month=pace.days_in_month,
            projected=pace.projected.amount,
            over_on=pace.over_on,
        )
