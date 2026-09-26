from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .direction import Direction


@dataclass(frozen=True, slots=True)
class MessageReading:
    """카드 문자를 읽은 결과. 못 읽은 칸은 None이다 — 추측으로 채우지 않는다.

    `refusal`이 있으면 읽지 않기로 한 것이고, 나머지 칸은 전부 비어 있다.
    """

    direction: Direction | None = None
    amount: int | None = None
    occurred_at: datetime | None = None  # aware
    account_id: str | None = None
    merchant: str | None = None
    refusal: str = ""
