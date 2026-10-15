"""`POST /insights` — 리포트의 "눈에 띈 것"(docs/ai/agentic-reports.md). plan-and-execute다.

리포트는 AI를 기다리지 않는다 — 화면은 고정 영역을 먼저 그리고 이 자리를 뒤에 채운다.
비어 있는 답(200)이면 화면은 그 영역을 그리지 않는다. 모델에 닿지 못하면 503이다.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import date
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from agent.application.dto import RunSeat
from agent.application.errors import ModelUnavailable
from agent.application.use_cases.run_records import failed_run, insight_run
from agent.interfaces.schemas import InsightRequest, InsightResponse
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/insights")
async def insights(body: InsightRequest, services: ServicesDep) -> InsightResponse:
    """그 달의 집계를 훑고, 더 볼 것을 계획하고, 차트 선언과 문장으로 조립한다. 쓰지 않는다."""
    run_id = str(uuid.uuid4())
    started = time.perf_counter()
    month = date.fromisoformat(f"{body.month}-01")
    try:
        found = await services.insights(month, body.local_now().date(), ZoneInfo(body.timezone))
    except ModelUnavailable as error:
        # 503도 실행이다 — 남기고 번역은 web_app의 처리기에 넘긴다
        await services.record(failed_run(run_id, RunSeat.INSIGHT, body.month, error))
        raise
    _log.info(
        "insights done run_id=%s stop=%s charts=%d highlights=%d elapsed_ms=%d",
        run_id,
        found.stop.value,
        len(found.charts),
        len(found.highlights),
        (time.perf_counter() - started) * 1000,
    )
    await services.record(insight_run(run_id, body.month, found))
    return InsightResponse.of(found)
