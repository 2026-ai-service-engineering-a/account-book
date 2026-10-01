from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str  # 기계가 읽는다. 부르는 쪽은 이걸로 분기한다
    message: str  # 사람이 읽는다
