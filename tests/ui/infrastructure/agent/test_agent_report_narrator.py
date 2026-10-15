from __future__ import annotations

import asyncio
import json
from collections.abc import Callable

import httpx

from tests.ui.conftest import FixedClock
from ui.application.dto import Period
from ui.infrastructure.agent import AgentReportNarrator

SEPTEMBER = Period(2026, 9)
REPLY = {
    "charts": [
        {
            "kind": "hbar",
            "title": "예산 대비",
            "unit": "KRW",
            "note": "",
            "points": [{"label": "생활", "value": 1092000, "annotated": True}],
        }
    ],
    "highlights": ["전자랜드에서 890000원이 지출되었습니다."],
}


def narrator(handler: Callable[[httpx.Request], httpx.Response]) -> AgentReportNarrator:
    transport = httpx.MockTransport(handler)
    return AgentReportNarrator("http://agent", "Asia/Seoul", FixedClock(), 1, transport=transport)


def narrate(handler: Callable[[httpx.Request], httpx.Response]):
    return asyncio.run(narrator(handler).narrate(SEPTEMBER, None, ()))  # type: ignore[arg-type]


def test_asks_for_the_month_and_reads_charts_and_sentences():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=REPLY)

    found = narrate(handler)
    body = json.loads(seen[0].content)
    assert seen[0].url.path == "/insights" and body["month"] == "2026-09"
    assert body["timezone"] == "Asia/Seoul" and "now" in body
    assert found is not None and found.charts[0].points[0].annotated
    assert found.highlights == ("전자랜드에서 890000원이 지출되었습니다.",)


def test_an_agent_that_is_down_or_odd_is_none_not_the_rule_phrases():
    assert narrate(lambda request: httpx.Response(503, json={})) is None
    assert narrate(lambda request: httpx.Response(200, json={"charts": "?"})) is None
