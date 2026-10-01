from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from ui.application.dto import BudgetStatus
from ui.application.values import Money

from .category_reply import CategoryReply


class BudgetStatusReply(BaseModel):
    """예산 한 줄. 소진율·페이스까지 api가 계산했다 — 화면은 나눗셈을 하지 않는다."""

    category: CategoryReply
    limit: int | None
    spent: int
    remaining: int | None
    percent: int | None
    projected: int | None
    over_on: date | None

    def status(self) -> BudgetStatus:
        return BudgetStatus(
            category=self.category.category(),
            limit=_money(self.limit),
            spent=Money(self.spent),
            remaining=_money(self.remaining),
            percent=self.percent,
            projected=_money(self.projected),
            over_on=self.over_on,
        )


def _money(amount: int | None) -> Money | None:
    return Money(amount) if amount is not None else None
