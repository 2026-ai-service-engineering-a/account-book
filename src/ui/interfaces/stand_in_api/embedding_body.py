from __future__ import annotations

from pydantic import BaseModel, Field

_VECTOR_LIMIT = 3072


class EmbeddingBody(BaseModel):
    model: str = Field(min_length=1)
    vector: list[float] = Field(min_length=1, max_length=_VECTOR_LIMIT)
