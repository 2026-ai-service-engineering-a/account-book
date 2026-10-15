"""감사 로그의 칸 — 실행의 자리·흐름·끝난 이유, 도구 호출의 call_id.

`agent_runs`·`tool_calls`는 첫 마이그레이션부터 있었지만 쓰는 코드가 없어 비어 있다. 그래서 새
칸을 기본값 없이 NOT NULL로 더한다 — 지어낸 값으로 옛 줄을 채울 일이 없다.

autogenerate는 CHECK 제약을 모른다. 자리·흐름·상태의 CHECK 셋은 손으로 넣었다
(development-rules 6.6 — 값의 목록은 enum이 아니라 CHECK).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-15 02:09:43+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("seat", sa.String(length=20), nullable=False))
    op.add_column("agent_runs", sa.Column("flow", sa.String(length=20), nullable=False))
    op.add_column("agent_runs", sa.Column("stop_reason", sa.String(length=30), nullable=False))
    op.create_check_constraint(
        op.f("ck_agent_runs_seat"), "agent_runs", "seat IN ('capture', 'classify', 'chat', 'ask')"
    )
    op.create_check_constraint(
        op.f("ck_agent_runs_flow"), "agent_runs", "flow IN ('single', 'react', 'plan_execute')"
    )
    op.create_check_constraint(
        op.f("ck_agent_runs_status"), "agent_runs", "status IN ('done', 'failed')"
    )
    # 제공자가 정하는 값이다. Gemini는 생각 서명을 붙여 150자를 넘긴다 — 길이를 못 박지 않는다
    op.add_column("tool_calls", sa.Column("call_id", sa.Text(), nullable=False))
    op.create_unique_constraint(
        op.f("uq_tool_calls_run_id_call_id"), "tool_calls", ["run_id", "call_id"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_tool_calls_run_id_call_id"), "tool_calls", type_="unique")
    op.drop_column("tool_calls", "call_id")
    op.drop_constraint(op.f("ck_agent_runs_status"), "agent_runs", type_="check")
    op.drop_constraint(op.f("ck_agent_runs_flow"), "agent_runs", type_="check")
    op.drop_constraint(op.f("ck_agent_runs_seat"), "agent_runs", type_="check")
    op.drop_column("agent_runs", "stop_reason")
    op.drop_column("agent_runs", "flow")
    op.drop_column("agent_runs", "seat")
