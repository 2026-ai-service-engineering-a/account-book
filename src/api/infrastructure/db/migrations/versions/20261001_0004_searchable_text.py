"""거래의 색인 텍스트와 해시 — 카테고리 고르기의 이력·벡터 검색이 이 열로 찾는다.

이미 있는 거래도 채운다. 정규화 규칙은 이 마이그레이션 안에 얼려 둔다 — 나중에 규칙이 바뀌어도
이 마이그레이션은 그때의 모양으로 돈다. 규칙을 바꾸면 새 마이그레이션이 다시 채운다.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-01 11:20:47.495683+00:00
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# domain/rules/searchable_text.py의 2026-10-01 모양
_BRANCH = re.compile(r"\s+\S*점$")
_COMPANY = re.compile(r"\(주\)|㈜|주식회사")
_SPACES = re.compile(r"\s+")


def _text(merchant: str, memo: str) -> str:
    name = _BRANCH.sub("", _COMPANY.sub("", merchant).strip())
    return _SPACES.sub(" ", f"{name} {memo}").strip()


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("search_text", sa.String(length=300), server_default="", nullable=False),
    )
    op.add_column(
        "transactions",
        sa.Column("text_hash", sa.String(length=64), server_default="", nullable=False),
    )
    op.create_index(op.f("ix_transactions_text_hash"), "transactions", ["text_hash"], unique=False)
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, merchant, memo FROM transactions")).all()
    for row in rows:
        text = _text(row.merchant, row.memo)
        connection.execute(
            sa.text("UPDATE transactions SET search_text = :t, text_hash = :h WHERE id = :id"),
            {
                "t": text,
                "h": hashlib.sha256(text.encode()).hexdigest()[:16] if text else "",
                "id": row.id,
            },
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_transactions_text_hash"), table_name="transactions")
    op.drop_column("transactions", "text_hash")
    op.drop_column("transactions", "search_text")
