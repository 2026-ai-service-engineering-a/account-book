from __future__ import annotations

from pydantic import BaseModel

from api.application.dto import MonthlyReport

from .category_change_body import CategoryChangeBody
from .month_total_body import MonthTotalBody
from .totals_body import TotalsBody


class MonthlyReportBody(BaseModel):
    """월간 리포트. 숫자는 전부 계산된 값이다 — 받는 쪽은 더하지 않는다."""

    period: str
    totals: TotalsBody
    previous: TotalsBody | None
    by_category: list[CategoryChangeBody]
    months: list[MonthTotalBody]
    through_day: int | None

    @classmethod
    def of(cls, report: MonthlyReport) -> MonthlyReportBody:
        return cls(
            period=str(report.period),
            totals=TotalsBody.of(report.totals),
            previous=TotalsBody.of(report.previous) if report.previous else None,
            by_category=[CategoryChangeBody.of(c) for c in report.by_category],
            months=[MonthTotalBody.of(m) for m in report.months],
            through_day=report.through_day,
        )
