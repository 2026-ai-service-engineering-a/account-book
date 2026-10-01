from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from api.domain.entities import Category
from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class BudgetStatus:
    """예산 한 줄. 소진율과 페이스까지 여기서 낸다 — 받는 쪽은 나눗셈을 하지 않는다."""

    category: Category
    limit: Money | None  # 정하지 않았으면 None
    spent: Money
    remaining: Money | None
    percent: int | None
    projected: Money | None  # 지금 페이스로 말일에 닿을 금액
    over_on: date | None  # 예산을 넘는(넘은) 날
