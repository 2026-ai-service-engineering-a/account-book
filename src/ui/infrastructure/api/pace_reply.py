from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from ui.application.dto import PaceSeries
from ui.application.values import Money

from .category_reply import CategoryReply


class PaceReply(BaseModel):
    category: CategoryReply
    limit: int
    cumulative: list[int]
    days_in_month: int
    projected: int
    over_on: date | None

    def series(self) -> PaceSeries:
        return PaceSeries(
            category=self.category.category(),
            limit=Money(self.limit),
            cumulative=tuple(Money(m) for m in self.cumulative),
            days_in_month=self.days_in_month,
            projected=Money(self.projected),
            over_on=self.over_on,
        )
