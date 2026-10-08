"""문서 Q&A의 저장 — documents와 document_chunks, 키워드 검색의 pg_trgm.

pg_trgm은 Postgres에 딸린 확장이라 DB 이미지에 이미 있다. 켜기만 한다. BM25 확장은 들이지
않는다(docs/ai/document-rag.md 7.2 — 형태소 없는 한국어에 쓸모 있는지부터 잰다).

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-08 12:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source", sa.String(length=300), nullable=False),
        sa.Column("mst", sa.String(length=20), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=300), nullable=False),
        sa.Column("document_id", sa.String(length=200), nullable=False),
        sa.Column("strategy", sa.String(length=20), nullable=False),
        sa.Column("heading", sa.String(length=300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "strategy IN ('fixed_500', 'paragraph', 'paragraph_item')",
            name=op.f("ck_document_chunks_strategy"),
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_chunks_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
    )
    op.create_index(
        "ix_document_chunks_search_text",
        "document_chunks",
        ["search_text"],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={"search_text": "gin_trgm_ops"},
    )
    op.create_index(
        "ix_document_chunks_document_strategy",
        "document_chunks",
        ["document_id", "strategy", "position"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_chunks_text_hash"), "document_chunks", ["text_hash"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunks_text_hash"), table_name="document_chunks")
    op.drop_index("ix_document_chunks_document_strategy", table_name="document_chunks")
    op.drop_index("ix_document_chunks_search_text", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    # pg_trgm은 끄지 않는다 — 다른 것이 쓰고 있을 수 있다
