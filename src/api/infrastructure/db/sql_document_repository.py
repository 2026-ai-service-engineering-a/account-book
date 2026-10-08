from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Float, delete, func, select, type_coerce
from sqlalchemy.orm import Session

from api.application.dto import ChunkHit, IndexText
from api.domain.entities import Document, DocumentChunk
from api.domain.values import ChunkId, ChunkStrategy, DocumentId

from .rows import DocumentChunkRow, DocumentRow, TextEmbeddingRow


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

    def nearest(
        self, vector: tuple[float, ...], model: str, strategy: ChunkStrategy, k: int
    ) -> tuple[ChunkHit, ...]:
        # 조각은 글의 해시로 text_embeddings와 잇는다. 같은 글을 가진 조각은 벡터 하나를 나눠 쓴다
        distance = TextEmbeddingRow.vector.cosine_distance(list(vector))
        statement = (
            select(
                DocumentChunkRow,
                type_coerce(1 - distance, Float).label("similarity"),
                DocumentRow.title,
                DocumentRow.effective_date,
            )
            .join(TextEmbeddingRow, TextEmbeddingRow.text_hash == DocumentChunkRow.text_hash)
            .join(DocumentRow, DocumentRow.id == DocumentChunkRow.document_id)
            .where(TextEmbeddingRow.model == model, DocumentChunkRow.strategy == strategy.value)
            .order_by(distance, DocumentChunkRow.document_id, DocumentChunkRow.position)
            .limit(k)
        )
        return tuple(
            ChunkHit(_chunk(row), float(value), title, effective)
            for row, value, title, effective in self._session.execute(statement)
        )

    def pending(self, model: str, limit: int) -> tuple[IndexText, ...]:
        embedded = select(TextEmbeddingRow.text_hash).where(TextEmbeddingRow.model == model)
        statement = (
            select(DocumentChunkRow.text_hash, DocumentChunkRow.search_text)
            .where(DocumentChunkRow.text_hash.not_in(embedded))
            .distinct()
            .order_by(DocumentChunkRow.text_hash)
            .limit(limit)
        )
        return tuple(IndexText(h, t) for h, t in self._session.execute(statement))


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
