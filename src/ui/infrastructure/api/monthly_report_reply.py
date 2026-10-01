from __future__ import annotations

from typing import TypedDict

from pydantic import BaseModel

from ui.application.dto import CategoryChange, MonthlyReport, MonthTotal, Period, Totals
from ui.application.values import Money

from .category_reply import CategoryReply


# 응답의 안쪽 모양. 이 클래스만 쓰는 TypedDict라 같은 파일에 둔다(development-rules 1.2의 예외).
class _Totals(TypedDict):
    expense: int
    income: int


class _Change(TypedDict):
    category: CategoryReply
    this_month: int
    last_month: int | None
    delta: int | None
    percent: int | None


class _Month(TypedDict):
    period: str
    expense: int
    income: int


class MonthlyReportReply(BaseModel):
    """api `/v1/reports/monthly`의 본문. 숫자는 전부 api가 계산했다 — 여기서 더하지 않는다."""

    period: str
    totals: _Totals
    previous: _Totals | None
    by_category: list[_Change]
    months: list[_Month]
    through_day: int | None

    def report(self) -> MonthlyReport:
        return MonthlyReport(
            period=_period(self.period),
            totals=_totals(self.totals),
            previous=_totals(self.previous) if self.previous else None,
            by_category=tuple(
                CategoryChange(
                    category=c["category"].category(),
                    this_month=Money(c["this_month"]),
                    last_month=_money(c["last_month"]),
                    delta=_money(c["delta"]),
                    percent=c["percent"],
                )
                for c in self.by_category
            ),
            months=tuple(
                MonthTotal(_period(m["period"]), Money(m["expense"]), Money(m["income"]))
                for m in self.months
            ),
            through_day=self.through_day,
        )


def _totals(body: _Totals) -> Totals:
    return Totals(Money(body["expense"]), Money(body["income"]))


def _money(amount: int | None) -> Money | None:
    return Money(amount) if amount is not None else None


def _period(text: str) -> Period:
    period = Period.parse(text)
    if period is None:
        raise ValueError(f"기간이 아니다: {text!r}")
    return period
