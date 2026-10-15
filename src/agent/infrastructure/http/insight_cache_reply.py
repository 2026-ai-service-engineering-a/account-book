from __future__ import annotations

from pydantic import BaseModel


class InsightCacheReply(BaseModel):
    """api `GET /v1/insights/cache/{key}`의 응답 본문. 없으면 body가 null이다."""

    body: dict[str, object] | None
