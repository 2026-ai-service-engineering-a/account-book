from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Identity, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class ToolCallRow(Base):
    """도구 호출 하나. 거부된 쓰기도 남는다 — 무엇을 하려다 막혔는지가 감사에서는 중요하다
    (docs/api-contract.md 4장)."""

    __tablename__ = "tool_calls"
    # 같은 도구를 두 번 부른 대화에서 어느 결과인지 가리는 키다(docs/ai/tools.md 3.1)
    __table_args__ = (UniqueConstraint("run_id", "call_id"),)

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("agent_runs.id"), index=True)
    # 제공자가 정한다. Gemini는 생각 서명을 붙여 150자를 넘기기도 해서 길이를 못 박지 않는다
    call_id: Mapped[str] = mapped_column(Text)
    tool: Mapped[str] = mapped_column(String(50))
    # 도구 인자와 결과는 모양이 도구마다 다르다. DB 경계에서만 Any다(development-rules 5.2)
    args: Mapped[dict[str, Any]] = mapped_column(JSONB)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
