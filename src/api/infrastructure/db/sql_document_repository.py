from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import delete
from sqlalchemy.orm import Session

from api.domain.entities import Document, DocumentChunk

from .rows import DocumentChunkRow, DocumentRow


class SqlDocumentRepository:
    """문서와 조각을 Postgres에. 조각은 문서마다 지우고 새로 넣는다 — 바꾸는 일은 없다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def replace(self, document: Document, chunks: Sequence[DocumentChunk]) -> None:
        self._session.merge(
            DocumentRow(
                id=document.id,
                title=document.title,
                source=document.source,
                mst=document.mst,
                effective_date=document.effective_date,
                body=document.body,
            )
        )
        self._session.execute(
            delete(DocumentChunkRow).where(DocumentChunkRow.document_id == document.id)
        )
        self._session.add_all(
            DocumentChunkRow(
                id=c.id,
                document_id=c.document_id,
                strategy=c.strategy.value,
                heading=c.heading,
                body=c.body,
                search_text=c.search_text,
                text_hash=c.text_hash,
                position=c.position,
            )
            for c in chunks
        )
        self._session.flush()
