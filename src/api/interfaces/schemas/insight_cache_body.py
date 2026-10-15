from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InsightCacheBody(BaseModel):
    """캐시 한 칸. 없으면 `body`가 null이다 — 없는 것은 오류가 아니라 처음이라는 뜻이다."""

    key: str
    # 모양은 agent가 정한다. 바깥과 닿는 자리라 Any다(development-rules 5.2)
    body: dict[str, Any] | None
