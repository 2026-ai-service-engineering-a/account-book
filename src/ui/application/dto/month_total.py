from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import Money

from .period import Period


@dataclass(frozen=True, slots=True)
class MonthTotal:
    period: Period
    expense: Money
    income: Money
