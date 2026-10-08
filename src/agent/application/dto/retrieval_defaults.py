from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import ChunkStrategy, SearchMode


@dataclass(frozen=True, slots=True)
class RetrievalDefaults:
    """묻는 쪽이 정하지 않았을 때 쓰는 찾기 설정 — DOC_CHUNK_STRATEGY·DOC_SEARCH_MODE·DOC_TOP_K.

    재서 골랐다(docs/ai/document-rag.md 6.3·7.2). 코드에 박지 않는다.
    """

    strategy: ChunkStrategy = ChunkStrategy.PARAGRAPH_ITEM
    mode: SearchMode = SearchMode.HYBRID
    k: int = 8
