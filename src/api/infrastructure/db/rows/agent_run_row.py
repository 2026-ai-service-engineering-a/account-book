from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class AgentRunRow(Base):
    """에이전트 실행 하나의 감사 기록. 발화 원문은 운영 로그가 아니라 여기에만 남는다
    (development-rules 6.4)."""

    __tablename__ = "agent_runs"
    __table_args__ = (
        CheckConstraint(
            "seat IN ('capture', 'classify', 'chat', 'ask', 'insight', 'mcp')", name="seat"
        ),
        CheckConstraint("flow IN ('single', 'react', 'plan_execute', 'direct')", name="flow"),
        CheckConstraint(
            "status IN ('done', 'failed', 'awaiting_confirmation', 'aborted')", name="status"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    seat: Mapped[str] = mapped_column(String(20))
    flow: Mapped[str] = mapped_column(String(20))
    utterance: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(100))
    steps: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    tokens: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6), default=Decimal(0), server_default="0"
    )
    status: Mapped[str] = mapped_column(String(30))  # awaiting_confirmation은 21자다
    # 자리마다 값이 다르다(answered·refused·abstained…). 목록을 못 박지 않는다
    stop_reason: Mapped[str] = mapped_column(String(30))
    # 외부 클라이언트가 MCP 초기화에서 댄 이름(docs/ai/mcp.md 9장). mcp 자리만 채운다
    client: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
