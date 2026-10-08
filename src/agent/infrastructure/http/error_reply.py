from __future__ import annotations

from typing import NotRequired, TypedDict

from pydantic import BaseModel


class _Error(TypedDict):
    code: str
    details: NotRequired[dict[str, str]]  # 비어 있으면 api가 빼고 보낸다


class ErrorReply(BaseModel):
    """api 에러 응답의 본문(api-contract 5장). `code`로 가르고 `message`는 읽지 않는다."""

    error: _Error
