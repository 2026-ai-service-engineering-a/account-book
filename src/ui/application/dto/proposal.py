from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ui.application.values import Money, ProposalId

from .direction import Direction


@dataclass(frozen=True, slots=True)
class Proposal:
    """에이전트가 올린 쓰기 제안. 확인 카드 한 장이 된다(chat.md 5장).

    `unsure`는 AI가 읽지 못해 기본값으로 둔 칸이다(category·account) — 카드가 밝힌다.
    """

    id: ProposalId
    occurred_on: date
    category_name: str
    direction: Direction
    amount: Money
    account_name: str
    merchant: str
    unsure: tuple[str, ...] = ()
