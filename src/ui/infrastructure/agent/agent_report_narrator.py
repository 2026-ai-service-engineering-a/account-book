from __future__ import annotations

import logging
from typing import Literal, TypedDict

import httpx
from pydantic import TypeAdapter, ValidationError

from ui.application.dto import (
    BudgetStatus,
    InsightChart,
    InsightPoint,
    MonthlyReport,
    Period,
    ReportInsight,
)
from ui.application.ports import Clock

_log = logging.getLogger(__name__)


# agent `POST /insights`의 응답 모양. 이 클래스들만 쓴다(development-rules 1.2의 예외).
class _Point(TypedDict):
    label: str
    value: int | float
    annotated: bool


class _Chart(TypedDict):
    kind: Literal["bar", "hbar", "line"]
    title: str
    unit: Literal["KRW", "count", "days"]
    note: str
    points: list[_Point]


class _Reply(TypedDict):
    charts: list[_Chart]
    highlights: list[str]


_REPLY = TypeAdapter(_Reply)


class AgentReportNarrator:
    """리포트의 "눈에 띈 것"의 진짜 — agent의 `POST /insights`(plan-and-execute, 캐시 있음).

    ui는 판단하지 않는다. agent가 없거나 죽으면 None — 화면은 그 영역을 그리지 않고 고정 리포트만
    남는다(docs/ai/agentic-reports.md 7장). 규칙 문구로 물러서지 않는다 — AI가 고른 것처럼 보인다.
    """

    def __init__(
        self,
        base_url: str,
        timezone: str,
        clock: Clock,
        timeout: float,
        transport: httpx.AsyncBaseTransport | None = None,  # 테스트가 가짜 agent를 끼운다
    ) -> None:
        self._base_url = base_url
        self._timezone = timezone
        self._clock = clock
        self._timeout = timeout
        self._transport = transport

    async def narrate(
        self, period: Period, report: MonthlyReport, budgets: tuple[BudgetStatus, ...]
    ) -> ReportInsight | None:
        body = {
            "month": str(period),
            "now": self._clock.now().isoformat(),
            "timezone": self._timezone,
        }
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.post("/insights", json=body)
            response.raise_for_status()
            reply = _REPLY.validate_json(response.content)
        except (httpx.HTTPError, ValidationError) as error:
            # 처리하는 곳이 여기라 한 번만 남긴다
            _log.warning("agent insights failed: %s", type(error).__name__)
            return None
        return ReportInsight(
            charts=tuple(
                InsightChart(
                    kind=c["kind"],
                    title=c["title"],
                    unit=c["unit"],
                    points=tuple(
                        InsightPoint(p["label"], p["value"], p["annotated"]) for p in c["points"]
                    ),
                    note=c["note"],
                )
                for c in reply["charts"]
            ),
            highlights=tuple(reply["highlights"]),
        )
