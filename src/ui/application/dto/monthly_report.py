from __future__ import annotations

from dataclasses import dataclass

from .category_change import CategoryChange
from .month_total import MonthTotal
from .period import Period
from .totals import Totals


@dataclass(frozen=True, slots=True)
class MonthlyReport:
    period: Period
    totals: Totals
    previous: Totals | None  # 첫 달이면 None — 비교 열을 숨긴다
    by_category: tuple[CategoryChange, ...]  # 이번 달 큰 순서
    months: tuple[MonthTotal, ...]  # 오래된 달부터. 기록이 있는 달만
    through_day: int | None  # 진행 중인 달이면 오늘 날짜

    @property
    def is_empty(self) -> bool:
        return self.totals.expense == 0 and self.totals.income == 0
