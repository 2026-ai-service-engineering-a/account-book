from __future__ import annotations

from pydantic import BaseModel, Field


class VersionReply(BaseModel):
    """api `GET /v1/stats/version`의 응답 본문 — 불투명한 글이다. 풀어 보지 않는다."""

    version: str = Field(min_length=1)
