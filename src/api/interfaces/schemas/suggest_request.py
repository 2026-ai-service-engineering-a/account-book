from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from api.application.dto import CategoryQuery
from api.domain.values import EMBEDDING_DIMENSIONS, Direction


class SuggestRequest(BaseModel):
    """`POST /v1/categories/suggest`의 본문.

    벡터는 agent가 계산해 넘긴다 — api는 임베딩 제공자를 모른다.
    """

    merchant: str = Field(default="", max_length=100)
    memo: str = Field(default="", max_length=200)
    direction: Literal["expense", "income"]
    embedding_model: str = ""
    query_vector: list[float] | None = Field(
        default=None, min_length=EMBEDDING_DIMENSIONS, max_length=EMBEDDING_DIMENSIONS
    )

    def query(self) -> CategoryQuery:
        return CategoryQuery(
            merchant=self.merchant,
            memo=self.memo,
            direction=Direction(self.direction),
            embedding_model=self.embedding_model,
            query_vector=tuple(self.query_vector) if self.query_vector else None,
        )
