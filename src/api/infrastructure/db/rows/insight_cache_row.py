from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class InsightCacheRow(Base):
    """리포트 AI 영역의 캐시(docs/ai/agentic-reports.md 8장). TTL이 없다 — 데이터가 바뀌면 키가
    바뀐다. 키는 agent가 period · data_version · prompt_version · model로 만든 해시다.

    api는 안을 읽지 않는다. 같은 키에 다시 쓰면 갈아 끼운다.
    """

    __tablename__ = "insight_cache"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    # 모양은 agent가 정한다. DB 경계에서만 Any다(development-rules 5.2)
    body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
