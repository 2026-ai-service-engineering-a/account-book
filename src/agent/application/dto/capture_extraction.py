from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Direction, PaymentMethod, SaidWhen

from .extraction_kind import ExtractionKind


@dataclass(frozen=True, slots=True)
class CaptureExtraction:
    """LLM이 한 줄에서 뽑은 값. 스키마 검사를 지났지만 아직 근거 검사 전이다.

    `amount`가 0이면 금액을 못 찾은 것이다. 날짜는 표현(`when`)만 있고, 실제 시각은
    유스케이스가 기준 시각으로 정한다.
    """

    kind: ExtractionKind
    amount: int
    direction: Direction | None
    payment_method: PaymentMethod | None
    merchant: str
    when: SaidWhen
