from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class DocumentChunkRow(Base):
    """검색의 단위. 청킹 전략마다 같은 문서의 조각이 따로 있다 — 전략끼리 견주려고
    (docs/ai/document-rag.md 7.2). `body`는 원문, 찾는 것은 `search_text`다.
    """

    __tablename__ = "document_chunks"
    __table_args__ = (
        CheckConstraint(
            "strategy IN ('fixed_500', 'paragraph', 'paragraph_item')", name="strategy"
        ),
        # 키워드 검색 — 글자 세 개짜리 조각(트라이그램)의 겹침으로 찾는다. 형태소 분석이 없어도 돈다
        Index(
            "ix_document_chunks_search_text",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
        Index("ix_document_chunks_document_strategy", "document_id", "strategy", "position"),
    )

    id: Mapped[str] = mapped_column(String(300), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        String(200), ForeignKey("documents.id", ondelete="CASCADE")
    )
    strategy: Mapped[str] = mapped_column(String(20))
    heading: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    search_text: Mapped[str] = mapped_column(Text)
    text_hash: Mapped[str] = mapped_column(String(64), index=True)  # text_embeddings와 잇는 열쇠
    position: Mapped[int] = mapped_column(Integer)
