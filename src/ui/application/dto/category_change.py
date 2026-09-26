from __future__ import annotations

from dataclasses import dataclass

from .category import Category


@dataclass(frozen=True, slots=True)
class CategoryChange:
    """리포트 표 한 줄. 증감은 api가 계산해서 준다."""

    category: Category
    this_month: int
    last_month: int | None  # 비교할 달이 없으면 None
    delta: int | None
    percent: int | None  # 지난달이 0이면 None
