from __future__ import annotations

from typing import Protocol

from ui.application.dto import MonthlyReport, PaceSeries, Period, Totals, TransactionFilter
from ui.application.values import CategoryId


class ReportGateway(Protocol):
    """api의 `/v1/summary`. 집계는 전부 저쪽이 한다 — 화면은 더하지 않는다."""

    async def totals(self, criteria: TransactionFilter) -> Totals: ...

    async def monthly(self, period: Period) -> MonthlyReport: ...

    async def pace(self, category_id: CategoryId, period: Period) -> PaceSeries | None:
        """예산이 없는 카테고리면 None."""
        ...
