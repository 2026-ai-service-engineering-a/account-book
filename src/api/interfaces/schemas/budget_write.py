from __future__ import annotations

from pydantic import BaseModel, StrictInt

from api.domain.values import Money


class BudgetWrite(BaseModel):
    """PUT /v1/budgets/{category_id}의 본문. `limit_amount`가 null이면 이번 달부터 예산 없음."""

    limit_amount: StrictInt | None

    def amount(self) -> Money | None:
        return Money(self.limit_amount) if self.limit_amount is not None else None
