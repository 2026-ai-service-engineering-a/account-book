from __future__ import annotations

from typing import Protocol

from ui.application.dto import BudgetStatus, Period
from ui.application.values import CategoryId, Money


class BudgetGateway(Protocol):
    """api의 `/v1/budgets`."""

    async def statuses(self, period: Period) -> tuple[BudgetStatus, ...]:
        """지출 카테고리 전부. 예산을 정하지 않은 것도 들어 있다."""
        ...

    async def status(self, category_id: CategoryId, period: Period) -> BudgetStatus: ...

    async def set_limit(
        self, category_id: CategoryId, amount: Money | None, idempotency_key: str
    ) -> BudgetStatus:
        """`None`이면 예산을 지운다."""
        ...
