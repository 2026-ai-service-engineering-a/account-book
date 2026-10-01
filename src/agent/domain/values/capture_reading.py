from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .direction import Direction
from .money import Money
from .payment_method import PaymentMethod


@dataclass(frozen=True, slots=True)
class CaptureReading:
    """한 줄을 읽은 결과. 못 읽은 칸은 None이다 — 추측으로 채우지 않는다.

    `refusal`이 있으면 읽지 않기로 한 것이고, 나머지 칸은 전부 비어 있다.
    """

    direction: Direction | None = None
    amount: Money | None = None
    occurred_at: datetime | None = None  # aware
    payment_method: PaymentMethod | None = None
    merchant: str | None = None
    refusal: str = ""

    def __post_init__(self) -> None:
        if self.occurred_at is not None and self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at은 aware여야 한다")
        if self.refusal and self.amount is not None:
            raise ValueError("읽지 않기로 했으면 칸을 채우지 않는다")

    @classmethod
    def refused(cls, reason: str) -> CaptureReading:
        return cls(refusal=reason)
