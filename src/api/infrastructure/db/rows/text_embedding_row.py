from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from api.domain.values import EMBEDDING_DIMENSIONS
from api.infrastructure.db.base import Base


class TextEmbeddingRow(Base):
    """색인 텍스트(가맹점 + 메모) 하나의 벡터. 거래가 아니라 텍스트에 붙는다 — 같은 가게
    백 건이 벡터 하나를 나눠 쓴다(category-suggestion-rag 4.2).

    `model`에는 차원이 붙어 있다("gemini/gemini-embedding-001@768"). 모델을 바꾸면 그 모델의
    행이 없으니 전부 다시 색인된다.
    """

    __tablename__ = "text_embeddings"
    __table_args__ = (
        # 코사인 거리(<=>)로 이웃을 찾는다. m·ef_construction은 pgvector의 기본값이다
        Index(
            "ix_text_embeddings_vector",
            "vector",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vector": "vector_cosine_ops"},
        ),
    )

    model: Mapped[str] = mapped_column(String(100), primary_key=True)
    text_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    vector: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
