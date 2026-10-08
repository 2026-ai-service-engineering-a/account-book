from __future__ import annotations

import dataclasses
from collections.abc import Callable

from api.application.dto import ChunkHit
from api.application.ports import UnitOfWork
from api.domain.errors import InvalidEmbedding
from api.domain.rules.rank_fusion import reciprocal_rank_fusion
from api.domain.values import EMBEDDING_DIMENSIONS, ChunkStrategy, SearchMode

DEFAULT_K = 5
MAX_K = 20
# 하이브리드가 두 검색에서 각각 받는 후보 수. k와 무관하게 두어 k가 달라도 위쪽 순위가 같다 —
# k=3의 결과가 k=8의 앞 셋이다. 조각이 전략마다 백 개 남짓이라 이 안에 웬만한 정답이 든다.
FUSION_POOL = 50


class SearchDocuments:
    """문서 조각 찾기 — 키워드·벡터·하이브리드(docs/ai/document-rag.md 7.2).

    점수로 거르지 않고 늘 k개를 낸다. 순위를 재야 하고, 모른다고 답할지는 생성 쪽이 정한다.
    벡터는 agent가 임베딩해 실어 준다 — api는 임베딩 제공자를 모른다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self,
        query: str,
        strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH,
        k: int = DEFAULT_K,
        mode: SearchMode = SearchMode.KEYWORD,
        vector: tuple[float, ...] | None = None,
        model: str = "",
    ) -> tuple[ChunkHit, ...]:
        words = " ".join(query.split())
        k = max(1, min(k, MAX_K))
        if mode is SearchMode.KEYWORD:
            if not words:
                return ()
            with self._unit_of_work() as uow:
                return uow.documents.search(words, strategy, k)
        if vector is None or not model:
            raise InvalidEmbedding(
                {"query_vector": "벡터·하이브리드 검색에는 질문 벡터와 모델이 필요합니다."}
            )
        if len(vector) != EMBEDDING_DIMENSIONS:
            raise InvalidEmbedding(
                {"query_vector": f"벡터는 {EMBEDDING_DIMENSIONS}차원이어야 합니다."}
            )
        with self._unit_of_work() as uow:
            if mode is SearchMode.VECTOR:
                return uow.documents.nearest(vector, model, strategy, k)
            pool = max(k, FUSION_POOL)
            lexical = uow.documents.search(words, strategy, pool) if words else ()
            semantic = uow.documents.nearest(vector, model, strategy, pool)
        return _fused(lexical, semantic, k)


def _fused(
    lexical: tuple[ChunkHit, ...], semantic: tuple[ChunkHit, ...], k: int
) -> tuple[ChunkHit, ...]:
    """두 순위를 RRF로. 점수 칸에는 합친 점수(순위의 역수 합)를 담는다 — 0~1의 유사도가 아니다."""
    by_id: dict[str, ChunkHit] = {h.chunk.id: h for h in (*lexical, *semantic)}
    fused = reciprocal_rank_fusion([[h.chunk.id for h in lexical], [h.chunk.id for h in semantic]])
    return tuple(dataclasses.replace(by_id[key], score=score) for key, score in fused[:k])
