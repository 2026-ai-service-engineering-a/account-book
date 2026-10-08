from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agent.domain.values import Amount, CategoryId


@dataclass(frozen=True, slots=True)
class BudgetLine:
    """get_budget_status 답의 한 줄. 예산을 정하지 않았으면 limit부터 아래가 None이다."""

    category_id: CategoryId
    name: str
    spent: Amount
    limit: Amount | None
    remaining: Amount | None
    percent: int | None
    projected: Amount | None  # 지금 페이스면 말일에 닿을 금액
    over_on: date | None  # 그 페이스로 예산을 넘는 날
