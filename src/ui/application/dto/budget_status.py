from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ui.application.values import Money

from .category import Category


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """예산 한 줄. 소진율과 페이스는 api가 계산한다 — 화면은 나눗셈을 하지 않는다."""

    category: Category
    limit: Money | None  # 정하지 않았으면 None
    spent: Money
    remaining: Money | None
    percent: int | None
    projected: Money | None  # 지금 페이스로 말일에 닿을 금액
    over_on: date | None  # 예산을 넘는(넘은) 날

    @property
    def is_over(self) -> bool:
        return self.limit is not None and self.spent > self.limit
