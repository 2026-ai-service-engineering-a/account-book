from __future__ import annotations

from pydantic import AwareDatetime, BaseModel

from api.application.dto import CategoryEvidence


class EvidenceBody(BaseModel):
    """근거가 된 과거 거래. 금액은 정수 원 — 프롬프트에 글자로 넣는 건 agent의 일이다."""

    transaction_id: str
    merchant: str
    memo: str
    category_id: str
    amount: int
    occurred_at: AwareDatetime
    similarity: float | None

    @classmethod
    def of(cls, evidence: CategoryEvidence) -> EvidenceBody:
        return cls(
            transaction_id=evidence.transaction_id,
            merchant=evidence.merchant,
            memo=evidence.memo,
            category_id=evidence.category_id,
            amount=evidence.amount.amount,
            occurred_at=evidence.occurred_at,
            similarity=evidence.similarity,
        )
