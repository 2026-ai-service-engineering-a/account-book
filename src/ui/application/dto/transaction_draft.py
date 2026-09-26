from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .direction import Direction


@dataclass(frozen=True, slots=True)
class TransactionDraft:
    """저장하기 전의 거래. 폼과 확인 카드가 같은 모양을 쓴다."""

    direction: Direction
    amount: int  # 정수 원. float는 쓰지 않는다
    occurred_at: datetime  # aware
    category_id: str
    account_id: str
    merchant: str = ""
    memo: str = ""
