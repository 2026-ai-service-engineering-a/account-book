from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, PeriodSpec


@dataclass(frozen=True, slots=True)
class ComparePeriodsInput:
    """a가 기준, b가 견줄 기간이다 — 증감은 b - a. "지난달보다 늘었어?"면 a=지난달, b=이번 달."""

    a: PeriodSpec
    b: PeriodSpec
    category_id: CategoryId | None = None
