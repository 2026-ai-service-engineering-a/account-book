"""예산은 바꿀 때까지 이어진다 — limit_amount가 비면 "이 달부터 예산 없음".

이어 쓰는 모델에서 예산을 지우려면 지웠다는 기록이 남아야 한다. 행을 지우면 그 앞 달의
예산이 다시 이어져 버린다. autogenerate는 CHECK 제약의 식이 바뀐 것을 모른다 — 손으로 썼다.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-01 12:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# 이름은 op.f로 감싼다. 감싸지 않으면 메타데이터의 이름 규칙이 한 번 더 붙는다
# (ck_budgets_ck_budgets_…).


def upgrade() -> None:
    op.drop_constraint(op.f("ck_budgets_limit_positive"), "budgets", type_="check")
    op.alter_column("budgets", "limit_amount", existing_type=sa.BigInteger(), nullable=True)
    op.create_check_constraint(
        op.f("ck_budgets_limit_positive"), "budgets", "limit_amount IS NULL OR limit_amount > 0"
    )


def downgrade() -> None:
    # "예산 없음" 기록은 되돌릴 모양이 없다. 지운다 — 그 달부터는 앞 달의 예산이 이어진다.
    op.execute("DELETE FROM budgets WHERE limit_amount IS NULL")
    op.drop_constraint(op.f("ck_budgets_limit_positive"), "budgets", type_="check")
    op.alter_column("budgets", "limit_amount", existing_type=sa.BigInteger(), nullable=False)
    op.create_check_constraint(op.f("ck_budgets_limit_positive"), "budgets", "limit_amount > 0")
