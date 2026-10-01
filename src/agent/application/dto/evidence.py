from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from agent.domain.values import CategoryId, Money


@dataclass(frozen=True, slots=True)
class Evidence:
    """검색이 찾은 과거 거래 하나 — RAG의 근거. 가맹점·메모는 사용자 데이터라 프롬프트에서 마커
    안에 넣는다."""

    transaction_id: str
    merchant: str
    memo: str
    category_id: CategoryId
    amount: Money
    day: date
    similarity: float | None  # 벡터 단계에서만 있다
