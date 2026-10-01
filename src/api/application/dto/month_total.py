from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import Money, Period


@dataclass(frozen=True, slots=True)
class MonthTotal:
    period: Period
    expense: Money
    income: Money
