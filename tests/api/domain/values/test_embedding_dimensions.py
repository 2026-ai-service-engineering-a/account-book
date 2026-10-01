from __future__ import annotations

from api.domain.values import EMBEDDING_DIMENSIONS


def test_under_the_hnsw_limit():
    # pgvector의 HNSW 인덱스는 2000차원까지 받는다
    assert EMBEDDING_DIMENSIONS == 768 < 2000
