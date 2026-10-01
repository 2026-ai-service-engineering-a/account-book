"""카테고리·결제수단의 표시 순서(position). 셀렉트가 이름순이면 "기타"가 둘째 줄에 온다.


Revision ID: 0002
Revises: 0001
Create Date: 2026-10-01 10:58:58.069756+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts", sa.Column("position", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column(
        "categories", sa.Column("position", sa.Integer(), server_default="0", nullable=False)
    )


def downgrade() -> None:
    op.drop_column("categories", "position")
    op.drop_column("accounts", "position")
