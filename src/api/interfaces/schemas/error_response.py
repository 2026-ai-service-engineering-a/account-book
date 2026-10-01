from __future__ import annotations

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .error_body import ErrorBody


class ErrorResponse(BaseModel):
    """모든 에러는 같은 모양이다(api-contract 5장). `request_id`는 아직 없다 — ui가 헤더로
    넘기기 시작하면 붙인다."""

    error: ErrorBody

    @classmethod
    def reply(
        cls, status: int, code: str, message: str, details: dict[str, str] | None = None
    ) -> JSONResponse:
        body = cls(error=ErrorBody(code=code, message=message, details=details))
        return JSONResponse(body.model_dump(exclude_none=True), status_code=status)
