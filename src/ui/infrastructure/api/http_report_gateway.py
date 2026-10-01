from __future__ import annotations

from typing import TypedDict

from pydantic import TypeAdapter, ValidationError

from ui.application.dto import MonthlyReport, PaceSeries, Period, Totals, TransactionFilter
from ui.application.errors import LedgerUnavailable
from ui.application.values import CategoryId, Money

from .api_client import ApiClient
from .monthly_report_reply import MonthlyReportReply
from .pace_reply import PaceReply


# 합계 응답의 모양. 이 게이트웨이만 쓰는 TypedDict라 같은 파일에 둔다(development-rules 1.2의 예외).
class _Totals(TypedDict):
    expense: int
    income: int


_TOTALS = TypeAdapter(_Totals)
_PACE: TypeAdapter[PaceReply | None] = TypeAdapter(PaceReply | None)


class HttpReportGateway:
    """집계의 진짜 — api의 `/v1/summary`, `/v1/reports/*`. 합계는 전부 저쪽이 낸다."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def totals(self, criteria: TransactionFilter) -> Totals:
        params: dict[str, str | int] = {"period": str(criteria.period)}
        if criteria.direction is not None:
            params["direction"] = criteria.direction.value
        if criteria.category_id is not None:
            params["category_id"] = criteria.category_id
        if criteria.query:
            params["q"] = criteria.query
        response = await self._client.request("GET", "/v1/summary", params=params)
        try:
            body = _TOTALS.validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
        return Totals(Money(body["expense"]), Money(body["income"]))

    async def monthly(self, period: Period) -> MonthlyReport:
        response = await self._client.request(
            "GET", "/v1/reports/monthly", params={"period": str(period)}
        )
        try:
            return MonthlyReportReply.model_validate_json(response.content).report()
        except (ValidationError, ValueError) as error:
            raise LedgerUnavailable("모르는 응답 모양") from error

    async def pace(self, category_id: CategoryId, period: Period) -> PaceSeries | None:
        params: dict[str, str | int] = {"category_id": category_id, "period": str(period)}
        response = await self._client.request("GET", "/v1/reports/pace", params=params)
        try:
            found = _PACE.validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
        return found.series() if found else None
