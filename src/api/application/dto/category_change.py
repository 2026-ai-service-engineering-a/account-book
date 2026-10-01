from __future__ import annotations

from dataclasses import dataclass

from api.domain.entities import Category
from api.domain.values import Money


@dataclass(frozen=True, slots=True)
class CategoryChange:
    """리포트 표 한 줄 — 이번 달과 지난달, 증감."""

    category: Category
    this_month: Money
    last_month: Money | None  # 비교할 달이 없으면 None
    delta: Money | None
    percent: int | None  # 지난달이 0이면 None
