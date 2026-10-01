from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from api.infrastructure.db.base import Base


class IdempotencyKeyRow(Base):
    """쓰기 요청 하나의 키와 그 응답(docs/api-contract.md 3장).

    `status_code`가 비어 있으면 처리 중이다 — 같은 키가 또 오면 `request_in_progress`.
    """

    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(200), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status_code: Mapped[int | None] = mapped_column(Integer)
    # 24시간이 지나면 지운다. 지우는 쿼리가 이 열로 찾는다
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
