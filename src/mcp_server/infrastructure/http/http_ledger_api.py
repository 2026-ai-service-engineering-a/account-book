from __future__ import annotations

from datetime import date

import httpx
from pydantic import BaseModel, ValidationError

from mcp_server.application.dto import LedgerFilter
from mcp_server.application.errors import LedgerUnavailable
from mcp_server.application.ports import Row
from mcp_server.domain.values import TimeRange

from .budget_status_reply import BudgetStatusReply
from .compare_reply import CompareReply
from .error_reply import ErrorReply
from .frequency_reply import FrequencyReply
from .totals_reply import TotalsReply

type _Params = dict[str, str | int]


class HttpLedgerApi:
    """api의 집계 넷을 HTTP로 부른다. 읽기만 한다 — 쓰는 엔드포인트를 부르는 코드가 없다.

    4xx와 에러 코드는 `LedgerRejected`, 닿지 못했거나 5xx거나 모르는 모양이면
    `LedgerUnavailable`. 재시도하지 않는다.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 api를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._transport = transport

    async def summary(self, where: LedgerFilter) -> Row:
        response = await self._get("/v1/summary", _filter(where))
        return self._parse(TotalsReply, response).row()

    async def frequency(self, where: LedgerFilter) -> Row:
        response = await self._get("/v1/stats/frequency", _filter(where))
        return self._parse(FrequencyReply, response).row()

    async def compare(self, a: TimeRange, b: TimeRange, category_id: str) -> list[Row]:
        params: _Params = {
            "a_from": a.start.isoformat(),
            "a_to": a.end.isoformat(),
            "b_from": b.start.isoformat(),
            "b_to": b.end.isoformat(),
        }
        if category_id:
            params["category_id"] = category_id
        response = await self._get("/v1/stats/compare", params)
        return self._parse(CompareReply, response).rows()

    async def budget_status(self, month: date, category_id: str) -> list[Row]:
        params: _Params = {"period": f"{month.year:04d}-{month.month:02d}"}
        if category_id:
            params["category_id"] = category_id
        response = await self._get("/v1/budgets/status", params)
        return self._parse(BudgetStatusReply, response).rows()

    async def _get(self, path: str, params: _Params) -> httpx.Response:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(path, params=params)
        except httpx.HTTPError as error:
            raise LedgerUnavailable(type(error).__name__) from error
        if response.is_client_error:
            raise ErrorReply.rejection(response)
        if response.is_error:
            raise LedgerUnavailable(f"HTTP {response.status_code}")
        return response

    @staticmethod
    def _parse[R: BaseModel](kind: type[R], response: httpx.Response) -> R:
        try:
            return kind.model_validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error


def _filter(where: LedgerFilter) -> _Params:
    """시각은 오프셋을 붙여 보낸다. `+`는 httpx가 %2B로 인코딩한다(api-contract 6장)."""
    params: _Params = {"from": where.period.start.isoformat(), "to": where.period.end.isoformat()}
    if where.category_id:
        params["category_id"] = where.category_id
    if where.text:
        params["q"] = where.text
    if where.direction is not None:
        params["direction"] = where.direction.value
    return params
