from __future__ import annotations

from typing import Literal

from pydantic import AwareDatetime, BaseModel

from agent.domain.values import CaptureReading


class CaptureResponse(BaseModel):
    """읽은 결과. 못 읽은 칸은 null이고, `refusal`이 있으면 칸이 전부 비어 있다.

    금액은 정수 원이다. 서식("5,000원")은 화면의 일이다.
    """

    direction: Literal["expense", "income"] | None
    amount: int | None
    occurred_at: AwareDatetime | None
    payment_method: Literal["card", "cash", "bank"] | None
    merchant: str | None
    refusal: str

    @classmethod
    def of(cls, reading: CaptureReading) -> CaptureResponse:
        return cls(
            direction=reading.direction.value if reading.direction else None,
            amount=reading.amount.amount if reading.amount else None,
            occurred_at=reading.occurred_at,
            payment_method=reading.payment_method.value if reading.payment_method else None,
            merchant=reading.merchant,
            refusal=reading.refusal,
        )
