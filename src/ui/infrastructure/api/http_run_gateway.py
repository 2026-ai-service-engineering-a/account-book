from __future__ import annotations

from pydantic import BaseModel, ValidationError

from ui.application.dto import RunDetail, RunFilter, RunPage
from ui.application.errors import LedgerUnavailable, TransactionNotFound
from ui.application.values import PageCursor, RunId

from .api_client import ApiClient
from .run_detail_reply import RunDetailReply
from .run_page_reply import RunPageReply


class HttpRunGateway:
    """`/v1/runs`의 진짜 — 읽기만. 메모리 대역(MemoryRunGateway)과 같은 포트를 채운다."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def page(
        self, criteria: RunFilter, cursor: PageCursor | None = None, limit: int = 30
    ) -> RunPage:
        params: dict[str, str | int] = {"limit": limit}
        if criteria.seat:
            params["seat"] = criteria.seat
        if criteria.status:
            params["status"] = criteria.status
        if cursor:
            params["cursor"] = cursor
        response = await self._client.request("GET", "/v1/runs", params=params)
        return _parse(RunPageReply, response.content).page()

    async def get(self, run_id: RunId) -> RunDetail | None:
        try:
            response = await self._client.request("GET", f"/v1/runs/{run_id}")
        except TransactionNotFound:  # api의 not_found — 이름은 거래지만 코드 하나를 옮긴 것이다
            return None
        return _parse(RunDetailReply, response.content).detail()


def _parse[R: BaseModel](kind: type[R], content: bytes) -> R:
    try:
        return kind.model_validate_json(content)
    except ValidationError as error:
        raise LedgerUnavailable("모르는 응답 모양") from error
