from __future__ import annotations

from collections.abc import Callable

from api.application.dto import ChunkHit
from api.application.ports import UnitOfWork
from api.domain.values import ChunkStrategy

DEFAULT_K = 5
MAX_K = 20


class SearchDocuments:
    """문서 조각의 키워드 검색 — 벡터 검색(doc-index)의 기준선이다(docs/ai/document-rag.md 7.2).

    점수로 거르지 않고 늘 k개를 낸다. 순위를 재야 하고, 모른다고 답할지는 생성 쪽이 정한다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self, query: str, strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH, k: int = DEFAULT_K
    ) -> tuple[ChunkHit, ...]:
        words = " ".join(query.split())
        if not words:
            return ()
        with self._unit_of_work() as uow:
            return uow.documents.search(words, strategy, max(1, min(k, MAX_K)))
