from __future__ import annotations

from typing import Protocol

from api.domain.values import CategoryId, Money, Period


class BudgetRepository(Protocol):
    """예산은 바꿀 때까지 이어진다. 어떤 달의 예산은 그 달까지 가장 늦게 정한 값이다."""

    def limits(self, period: Period) -> dict[CategoryId, Money]:
        """그 달에 걸린 예산. 정하지 않았거나 "예산 없음"으로 바꾼 카테고리는 없다."""
        ...

    def set_limit(self, category_id: CategoryId, period: Period, amount: Money | None) -> None:
        """그 달부터 이 예산. `None`이면 그 달부터 예산 없음."""
        ...
