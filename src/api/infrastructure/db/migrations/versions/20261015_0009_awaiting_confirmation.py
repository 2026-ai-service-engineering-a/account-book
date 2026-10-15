"""감사 로그의 상태에 awaiting_confirmation·aborted — 쓰기 제안이 사람을 기다린다.

채팅의 기록은 제안을 감사 테이블에 대기로 넣고, 확인되면 done, 취소·만료면 aborted로 닫는다
(docs/ai/chat-capture.md 결정 5, agent-loop 6·9장). 값의 목록은 CHECK다 — 제약만 바꿔 끼운다.
칸도 넓힌다 — `awaiting_confirmation`은 21자라 String(20)에 들어가지 않는다.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-15 08:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NAME = "ck_agent_runs_status"


def upgrade() -> None:
    op.alter_column(
        "agent_runs", "status", type_=sa.String(length=30), existing_type=sa.String(length=20)
    )
    op.drop_constraint(op.f(_NAME), "agent_runs", type_="check")
    op.create_check_constraint(
        op.f(_NAME),
        "agent_runs",
        "status IN ('done', 'failed', 'awaiting_confirmation', 'aborted')",
    )


def downgrade() -> None:
    # 대기·중단 줄이 있으면 되돌릴 수 없다 — 지어낸 상태로 바꾸지 않고 실패하게 둔다
    op.drop_constraint(op.f(_NAME), "agent_runs", type_="check")
    op.create_check_constraint(op.f(_NAME), "agent_runs", "status IN ('done', 'failed')")
    op.alter_column(
        "agent_runs", "status", type_=sa.String(length=20), existing_type=sa.String(length=30)
    )
