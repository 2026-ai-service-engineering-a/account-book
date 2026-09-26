from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from ui.application.dto import Direction


@dataclass(frozen=True, slots=True)
class ParsedUtterance:
    amount: int | None
    day_offset: int  # 0 오늘, -1 어제
    at: time | None  # 끼니 낱말이 있으면 그 시각
    account_id: str
    direction: Direction
    merchant: str
    is_question: bool
    previous_month: bool
