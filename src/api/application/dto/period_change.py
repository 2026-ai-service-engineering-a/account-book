from __future__ import annotations

from dataclasses import dataclass

from api.domain.entities import Category
from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class PeriodChange:
    """두 기간 비교의 한 줄 — 카테고리 하나의 a 합, b 합, 증감(b - a)."""

    category: Category
    a: Money
    b: Money
    delta: Money
    percent: int | None  # a가 0이면 None
