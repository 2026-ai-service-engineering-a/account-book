from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agent.domain.values import Direction


@dataclass(frozen=True, slots=True)
class RecordCard:
    """확인 카드 한 장(ui_docs/pages/chat.md 5.1). `proposal_id`는 그 제안의 `run_id`다.

    `unsure`는 AI가 읽지 못해 기본값으로 둔 칸이다 — 카드가 밝힌다(chat-capture 결정 8·9).
    """

    proposal_id: str
    occurred_on: date
    category_name: str
    direction: Direction
    amount: int
    account_name: str
    merchant: str
    unsure: tuple[str, ...] = ()
