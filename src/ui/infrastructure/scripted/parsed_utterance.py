from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from ui.application.dto import Direction
from ui.application.values import AccountId, Money


@dataclass(frozen=True, slots=True)
class ParsedUtterance:
    amount: Money | None
    day_offset: int  # 0 오늘, -1 어제
    day_said: bool  # "오늘·어제"를 말했나 — 말하지 않았으면 날짜를 채우지 않는다
    at: time | None  # "오후 3시"나 끼니 낱말이 있으면 그 시각
    account_id: AccountId | None  # 말하지 않았으면 None
    direction: Direction
    merchant: str
    is_question: bool
    previous_month: bool
