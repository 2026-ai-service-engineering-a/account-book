from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import Direction


@dataclass(frozen=True, slots=True)
class CategoryQuery:
    """카테고리 검색 한 번. 벡터는 agent가 계산해 넘긴다 — api는 임베딩 제공자를 모른다.

    `embedding_model`이 비면 벡터 단계를 건너뛴다.
    """

    merchant: str
    memo: str
    direction: Direction
    embedding_model: str = ""
    query_vector: tuple[float, ...] | None = None
