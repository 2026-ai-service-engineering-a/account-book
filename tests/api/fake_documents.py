"""문서 저장소의 가짜 — 메모리 위의 문서와 조각."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from api.application.dto import ChunkHit
from api.domain.entities import Document, DocumentChunk
from api.domain.values import ChunkStrategy, DocumentId


class FakeDocuments:
    def __init__(self) -> None:
        self.documents: dict[DocumentId, Document] = {}
        self.chunks: dict[str, DocumentChunk] = {}

    def replace(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        self.documents[document.id] = document
        self.chunks = {k: c for k, c in self.chunks.items() if c.document_id != document.id}
        self.chunks.update((c.id, c) for c in chunks)

    def search(self, query: str, strategy: ChunkStrategy, k: int) -> tuple[ChunkHit, ...]:
        """글자 세 개짜리 조각의 겹침으로 잰다 — pg_trgm을 거칠게 흉내 낸다."""
        wanted = _trigrams(query)
        hits = [
            ChunkHit(c, len(wanted & _trigrams(c.search_text)) / (len(wanted) or 1), *self._of(c))
            for c in self.chunks.values()
            if c.strategy is strategy
        ]
        hits.sort(key=lambda h: (-h.score, h.chunk.document_id, h.chunk.position))
        return tuple(hits[:k])

    def _of(self, chunk: DocumentChunk) -> tuple[str, date]:
        document = self.documents[chunk.document_id]
        return document.title, document.effective_date


def _trigrams(text: str) -> set[str]:
    padded = f"  {text} "
    return {padded[i : i + 3] for i in range(len(padded) - 2)}
