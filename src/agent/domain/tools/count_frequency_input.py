from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Direction, PeriodSpec


@dataclass(frozen=True, slots=True)
class CountFrequencyInput:
    period: PeriodSpec
    category_id: CategoryId | None = None
    merchant: str = ""  # 가맹점·메모에 든 글자(부분 일치)
    direction: Direction = Direction.EXPENSE  # 수입과 섞으면 회당 평균이 뜻을 잃는다
