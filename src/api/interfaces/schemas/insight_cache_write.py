from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class InsightCacheWrite(BaseModel):
    """`PUT /v1/insights/cache/{key}`의 본문. api는 안을 읽지 않는다."""

    body: dict[str, Any]
