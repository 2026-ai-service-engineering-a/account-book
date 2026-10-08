from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """`POST /ask`의 본문 — 질문 하나. 찾는 방법은 agent의 기본값(DOC_*)이다."""

    q: str = Field(min_length=1, max_length=200)
