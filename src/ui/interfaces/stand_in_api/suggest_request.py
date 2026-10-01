from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ui.application.dto import CategoryQuery, Direction

# gemini-embedding-001이 낼 수 있는 가장 긴 벡터. 넘으면 벡터가 아니다.
_VECTOR_LIMIT = 3072


class SuggestRequest(BaseModel):
    merchant: str = Field(default="", max_length=100)
    memo: str = Field(default="", max_length=200)
    direction: Literal["expense", "income"]
    embedding_model: str = ""
    query_vector: list[float] | None = Field(default=None, min_length=1, max_length=_VECTOR_LIMIT)

    def query(self) -> CategoryQuery:
        return CategoryQuery(
            merchant=self.merchant,
            memo=self.memo,
            direction=Direction(self.direction),
            embedding_model=self.embedding_model,
            query_vector=tuple(self.query_vector) if self.query_vector else None,
        )
