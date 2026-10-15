"""리포트 캐시 — 거래·예산의 updated_at과 insight_cache(docs/ai/agentic-reports.md 8장).

캐시 키의 data_version은 "건수 + 마지막 변경 시각"이다. 거래에 created_at만 있어서 고친
거래(PATCH)를 알아챌 수 없었다. 이미 있는 거래의 updated_at은 created_at으로 맞춘다 —
마이그레이션 시각으로 채우면 아무것도 안 바뀌었는데 바뀐 것처럼 보인다. 예산에는 시각이
없었으니 지금으로 둔다.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-15 06:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "insight_cache",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_insight_cache")),
    )
    op.add_column(
        "budgets",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute("UPDATE transactions SET updated_at = created_at")


def downgrade() -> None:
    op.drop_column("transactions", "updated_at")
    op.drop_column("budgets", "updated_at")
    op.drop_table("insight_cache")
