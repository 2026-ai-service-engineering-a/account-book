from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    """`POST /retrieve`의 본문 — 질문과 찾는 방법. 비운 것은 agent의 기본값(DOC_*)을 쓴다."""

    q: str = Field(min_length=1, max_length=200)
    k: int | None = Field(default=None, ge=1, le=20)
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"] | None = None
    mode: Literal["keyword", "vector", "hybrid"] | None = None
