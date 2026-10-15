from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Direction, PeriodSpec


@dataclass(frozen=True, slots=True)
class DetectOutliersInput:
    """판정 기준은 없다 — api가 정한다(api-contract 6장). 기간과 걸름만 넘긴다."""

    period: PeriodSpec
    category_id: CategoryId | None = None
    merchant: str = ""  # 가맹점·메모에 든 글자(부분 일치)
    direction: Direction = Direction.EXPENSE
