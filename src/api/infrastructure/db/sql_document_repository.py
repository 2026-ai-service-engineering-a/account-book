from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Float, delete, func, select
from sqlalchemy.orm import Session

from api.application.dto import ChunkHit
from api.domain.entities import Document, DocumentChunk
from api.domain.values import ChunkId, ChunkStrategy, DocumentId

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

    def search(self, query: str, strategy: ChunkStrategy, k: int) -> tuple[ChunkHit, ...]:
        # word_similarity(q, 글): 질문의 트라이그램이 글의 가장 비슷한 구간과 얼마나 겹치나.
        # 긴 조각이 짧은 질문 때문에 손해 보지 않는다(similarity는 글 전체 길이로 나눈다)
        score = func.word_similarity(query, DocumentChunkRow.search_text, type_=Float).label(
            "score"
        )
        statement = (
            select(DocumentChunkRow, score, DocumentRow.title, DocumentRow.effective_date)
            .join(DocumentRow, DocumentRow.id == DocumentChunkRow.document_id)
            .where(DocumentChunkRow.strategy == strategy.value)
            .order_by(score.desc(), DocumentChunkRow.document_id, DocumentChunkRow.position)
            .limit(k)
        )
        return tuple(
            ChunkHit(_chunk(row), float(value), title, effective)
            for row, value, title, effective in self._session.execute(statement)
        )


def _chunk(row: DocumentChunkRow) -> DocumentChunk:
    return DocumentChunk(
        id=ChunkId(row.id),
        document_id=DocumentId(row.document_id),
        strategy=ChunkStrategy(row.strategy),
        heading=row.heading,
        body=row.body,
        search_text=row.search_text,
        text_hash=row.text_hash,
        position=row.position,
    )
