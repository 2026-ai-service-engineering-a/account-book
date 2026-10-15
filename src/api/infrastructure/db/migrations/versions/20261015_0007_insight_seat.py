"""감사 로그의 자리에 insight — 리포트의 "눈에 띈 것"(docs/ai/agentic-reports.md).

값의 목록은 CHECK다. 늘릴 때 제약만 바꿔 끼운다(development-rules 6.6).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-15 05:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NAME = "ck_agent_runs_seat"


def upgrade() -> None:
    op.drop_constraint(op.f(_NAME), "agent_runs", type_="check")
    op.create_check_constraint(
        op.f(_NAME), "agent_runs", "seat IN ('capture', 'classify', 'chat', 'ask', 'insight')"
    )


def downgrade() -> None:
    # insight 줄이 있으면 되돌릴 수 없다 — 지어낸 자리로 바꾸지 않고 실패하게 둔다
    op.drop_constraint(op.f(_NAME), "agent_runs", type_="check")
    op.create_check_constraint(
        op.f(_NAME), "agent_runs", "seat IN ('capture', 'classify', 'chat', 'ask')"
    )
