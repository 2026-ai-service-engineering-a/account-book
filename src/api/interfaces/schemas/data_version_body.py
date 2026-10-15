from __future__ import annotations

from pydantic import BaseModel


class DataVersionBody(BaseModel):
    """`GET /v1/stats/version`의 답 — 불투명한 글. 같으면 데이터가 그대로다."""

    version: str
