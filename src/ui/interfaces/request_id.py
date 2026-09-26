"""요청마다 id를 붙인다. 에러 화면에 보여 줘서 문의할 때 쓰게 한다(ui-design 3장)."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import NewType

from fastapi import Request, Response

# 로그 상관관계 id. ui가 만들어 끝까지 전파하고, 에러 화면에 보여 준다.
RequestId = NewType("RequestId", str)


async def assign_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.request_id = RequestId(uuid.uuid4().hex[:16])
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


def request_id_of(request: Request) -> RequestId:
    return RequestId(str(getattr(request.state, "request_id", "-")))
