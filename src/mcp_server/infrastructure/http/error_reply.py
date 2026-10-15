from __future__ import annotations

from typing import NotRequired, TypedDict

import httpx
from pydantic import BaseModel, ValidationError

from mcp_server.application.errors import LedgerRejected, LedgerUnavailable


class _Error(TypedDict):
    code: str
    details: NotRequired[dict[str, str]]  # 비어 있으면 api가 빼고 보낸다


class ErrorReply(BaseModel):
    """api 에러 응답의 본문(api-contract 5장). `code`로 가르고 `message`는 읽지 않는다."""

    error: _Error

    @classmethod
    def rejection(cls, response: httpx.Response) -> LedgerUnavailable:
        """4xx 본문의 `code`를 읽는다. 모르는 모양의 4xx는 거절이 아니라 고장이다."""
        try:
            error = cls.model_validate_json(response.content).error
        except ValidationError:
            return LedgerUnavailable(f"HTTP {response.status_code}")
        return LedgerRejected(response.status_code, error["code"], error.get("details", {}))
