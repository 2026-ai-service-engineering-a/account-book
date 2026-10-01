from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ui.application.values import CategoryId, Money, TransactionId


@dataclass(frozen=True, slots=True)
class CategoryEvidence:
    """판단의 재료가 된 과거 거래 하나. LLM 프롬프트의 근거 줄이 된다."""

    transaction_id: TransactionId
    merchant: str
    memo: str
    category_id: CategoryId
    amount: Money
    occurred_at: datetime
    similarity: float | None = None  # 벡터 단계에서만 있다
