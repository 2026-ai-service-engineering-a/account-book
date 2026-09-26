from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .direction import Direction


@dataclass(frozen=True, slots=True)
class Proposal:
    """에이전트가 올린 쓰기 제안. 확인 카드 한 장이 된다(chat.md 5장)."""

    id: str
    occurred_on: date
    category_name: str
    direction: Direction
    amount: int
    account_name: str
    merchant: str
