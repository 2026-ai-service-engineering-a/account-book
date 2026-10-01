from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str  # 기계가 읽는다(api-contract 5장)
    message: str  # 사람이 읽는다
    details: dict[str, str] | None = None
