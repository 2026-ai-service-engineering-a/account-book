from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, PeriodName, PeriodSpec

_MONTHS = (PeriodName.THIS_MONTH, PeriodName.LAST_MONTH, PeriodName.MONTH)


@dataclass(frozen=True, slots=True)
class GetBudgetStatusInput:
    """예산은 달 단위다(api-contract 6장). 주·일 기간은 받지 않는다."""

    period: PeriodSpec
    category_id: CategoryId | None = None

    def __post_init__(self) -> None:
        if self.period.name not in _MONTHS:
            raise ValueError("예산은 달 단위다 — this_month, last_month, month 중 하나")
