from __future__ import annotations

import asyncio

import httpx
import pytest

from tests.ui.infrastructure.api.conftest import MONTHLY, PACE, client, recorder
from ui.application.dto import Period, TransactionFilter
from ui.application.errors import LedgerUnavailable
from ui.application.ports import ReportGateway
from ui.application.values import CategoryId, Money
from ui.infrastructure.api import HttpReportGateway


def gateway(body: object, status: int = 200):
    handler, seen = recorder(status, body)
    return HttpReportGateway(client(handler)), seen


def test_fills_the_port_and_sends_the_filter():
    port: ReportGateway
    port, seen = gateway({"expense": 1, "income": 2})
    totals = asyncio.run(port.totals(TransactionFilter(Period(2026, 9), query="김밥")))
    assert totals.expense == Money(1) and seen[0].url.path == "/v1/summary"
    assert dict(seen[0].url.params) == {"period": "2026-09", "q": "김밥"}


def test_monthly():
    port, seen = gateway(MONTHLY)
    report = asyncio.run(port.monthly(Period(2026, 9)))
    assert report.through_day == 3 and seen[0].url.params["period"] == "2026-09"


def test_pace_or_none():
    port, _ = gateway(PACE)
    assert asyncio.run(port.pace(CategoryId("food"), Period(2026, 9))) is not None
    # api는 예산이 없으면 JSON null을 낸다(본문이 비어 있는 게 아니다)
    null = HttpReportGateway(client(lambda request: httpx.Response(200, content=b"null")))
    assert asyncio.run(null.pace(CategoryId("cafe"), Period(2026, 9))) is None


def test_strange_body_is_unavailable():
    port, _ = gateway({"expense": "many"})
    with pytest.raises(LedgerUnavailable):
        asyncio.run(port.totals(TransactionFilter(Period(2026, 9))))
