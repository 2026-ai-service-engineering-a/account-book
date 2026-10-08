from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Amount, CategoryId


@dataclass(frozen=True, slots=True)
class CategoryShift:
    """compare_periods 답의 한 줄 — 카테고리 하나의 a 합, b 합, 증감(b - a)."""

    category_id: CategoryId
    name: str
    a: Amount
    b: Amount
    delta: Amount
    percent: int | None  # a 대비 절댓값. a가 0이면 None
