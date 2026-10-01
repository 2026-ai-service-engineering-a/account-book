from __future__ import annotations

from pydantic import AwareDatetime, BaseModel


class EvidenceBody(BaseModel):
    transaction_id: str
    merchant: str
    memo: str
    category_id: str
    amount: int  # 정수 원. 서식은 받는 쪽의 일이다
    occurred_at: AwareDatetime
    similarity: float | None
