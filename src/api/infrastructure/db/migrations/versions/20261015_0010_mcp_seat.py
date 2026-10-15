"""감사 로그에 mcp 자리 — 외부 AI 클라이언트의 도구 호출(docs/ai/mcp.md 9장).

자리에 `mcp`, 흐름에 `direct`(LLM 없이 도구 하나)를 더하고, 클라이언트가 초기화에서 댄 이름을
담을 `client` 칸을 둔다. 다른 자리는 비워 둔다. 값의 목록은 CHECK다 — 제약만 바꿔 끼운다.

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-15 10:00:00+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEAT = "ck_agent_runs_seat"
_FLOW = "ck_agent_runs_flow"
_SEATS = "'capture', 'classify', 'chat', 'ask', 'insight'"
_FLOWS = "'single', 'react', 'plan_execute'"


def upgrade() -> None:
    op.add_column("agent_runs", sa.Column("client", sa.String(length=100), nullable=True))
    _swap(_SEAT, f"seat IN ({_SEATS}, 'mcp')")
    _swap(_FLOW, f"flow IN ({_FLOWS}, 'direct')")


def downgrade() -> None:
    # mcp 줄이 있으면 되돌릴 수 없다 — 지어낸 자리로 바꾸지 않고 실패하게 둔다
    _swap(_FLOW, f"flow IN ({_FLOWS})")
    _swap(_SEAT, f"seat IN ({_SEATS})")
    op.drop_column("agent_runs", "client")


def _swap(name: str, condition: str) -> None:
    op.drop_constraint(op.f(name), "agent_runs", type_="check")
    op.create_check_constraint(op.f(name), "agent_runs", condition)
