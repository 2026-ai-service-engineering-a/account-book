from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.application.use_cases.search_documents import DEFAULT_K, MAX_K


class DocumentSearchRequest(BaseModel):
    """`POST /v1/documents/search`의 본문. 벡터·하이브리드는 agent가 임베딩한 질문 벡터를 싣는다."""

    q: str = Field(min_length=1, max_length=200)
    k: int = Field(default=DEFAULT_K, ge=1, le=MAX_K)
    strategy: Literal["fixed_500", "paragraph", "paragraph_item"] = "paragraph"
    mode: Literal["keyword", "vector", "hybrid"] = "keyword"
    embedding_model: str = Field(default="", max_length=100)
    query_vector: list[float] | None = None
