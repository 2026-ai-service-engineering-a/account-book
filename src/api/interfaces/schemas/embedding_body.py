from __future__ import annotations

from pydantic import BaseModel, Field


class EmbeddingBody(BaseModel):
    """`PUT /v1/embeddings/{text_hash}`의 본문. 차원 검사는 유스케이스가 한다 — 422의 문구를
    사람이 읽을 수 있게."""

    model: str = Field(min_length=1, max_length=100)
    vector: list[float] = Field(min_length=1)
