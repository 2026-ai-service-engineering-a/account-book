from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import Direction


@dataclass(frozen=True, slots=True)
class CategoryQuery:
    """api에 묻는 검색 한 번. 벡터가 필요하면 agent가 임베딩해서 다시 묻는다."""

    merchant: str
    memo: str
    direction: Direction
    embedding_model: str = ""  # 비면 벡터 단계를 건너뛴다
    query_vector: tuple[float, ...] | None = None
