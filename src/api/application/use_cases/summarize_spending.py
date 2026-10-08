from __future__ import annotations

from collections.abc import Callable
from datetime import tzinfo

from api.application.dto import Totals, TransactionQuery
from api.application.ports import UnitOfWork
from api.domain.rules import period_bounds
from api.domain.values import CategoryId, Direction, Period, TimeRange


class SummarizeSpending:
    """걸름에 맞는 지출 합과 수입 합 — `summarize_spending` 도구의 자리(api-contract 6장)."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], zone: tzinfo) -> None:
        self._unit_of_work = unit_of_work
        self._zone = zone

    def __call__(
        self,
        period: Period | TimeRange | None = None,
        direction: Direction | None = None,
        category_id: CategoryId | None = None,
        text: str = "",
    ) -> Totals:
        start, end = period_bounds.bounds(period, self._zone)
        query = TransactionQuery(
            start=start, end=end, direction=direction, category_id=category_id, text=text.strip()
        )
        with self._unit_of_work() as uow:
            return uow.stats.totals(query)
