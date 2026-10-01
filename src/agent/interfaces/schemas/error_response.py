from __future__ import annotations

from pydantic import BaseModel

from .error_body import ErrorBody


class ErrorResponse(BaseModel):
    """에러는 api와 같은 봉투로 낸다(docs/api-contract.md 5장)."""

    error: ErrorBody

    @classmethod
    def of(cls, code: str, message: str) -> ErrorResponse:
        return cls(error=ErrorBody(code=code, message=message))
