from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agent.domain.values import Amount, CategoryId, Direction


@dataclass(frozen=True, slots=True)
class TransactionLine:
    """거래 목록의 한 줄. 가맹점·메모는 사용자 데이터다 — 프롬프트에서 마커 안에 넣는다."""

    id: str
    occurred_at: datetime
    direction: Direction
    amount: Amount
    category_id: CategoryId
    merchant: str
    memo: str
