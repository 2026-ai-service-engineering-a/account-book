from __future__ import annotations

from dataclasses import dataclass

from .period import Period


@dataclass(frozen=True, slots=True)
class MonthTotal:
    period: Period
    expense: int
    income: int
