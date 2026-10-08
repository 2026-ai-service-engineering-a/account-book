from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RetrieveRequest(BaseModel):
    """`POST /retrieve`의 본문 — 질문과 찾는 방법. 기본값은 재서 정한다(document-rag.md 7.2)."""

    q: str = Field(min_length=1, max_length=200)
    k: int = Field(default=5, ge=1, le=20)
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"] = "paragraph"
    mode: Literal["keyword", "vector", "hybrid"] = "keyword"
