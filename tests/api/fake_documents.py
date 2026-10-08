"""문서 저장소의 가짜 — 메모리 위의 문서와 조각."""

from __future__ import annotations

from collections.abc import Sequence

from api.domain.entities import Document, DocumentChunk
from api.domain.values import DocumentId


class FakeDocuments:
    def __init__(self) -> None:
        self.documents: dict[DocumentId, Document] = {}
        self.chunks: dict[str, DocumentChunk] = {}

    def replace(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        self.documents[document.id] = document
        self.chunks = {k: c for k, c in self.chunks.items() if c.document_id != document.id}
        self.chunks.update((c.id, c) for c in chunks)
