from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter

from agent.application.dto import RunSeat
from agent.application.errors import ModelUnavailable
from agent.application.use_cases.run_records import capture_run, failed_run
from agent.interfaces.schemas import CaptureRequest, CaptureResponse
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/capture")
async def capture(body: CaptureRequest, services: ServicesDep) -> CaptureResponse:
    """한 줄을 거래 칸으로 읽는다. 쓰지 않는다 — 저장은 ui의 폼이 사람 손으로 한다."""
    run_id = str(uuid.uuid4())
    started = time.perf_counter()
    try:
        reading = await services.read_capture(body.text, body.local_now())
    except ModelUnavailable as error:
        # 503도 실행이다 — 남기고 번역은 web_app의 처리기에 넘긴다
        await services.record(failed_run(run_id, RunSeat.CAPTURE, body.text, error))
        raise
    # 운영 로그에는 원문·금액·가맹점을 남기지 않는다(development-rules 6.4)
    _log.info(
        "capture done run_id=%s refused=%s elapsed_ms=%d",
        run_id,
        bool(reading.refusal),
        (time.perf_counter() - started) * 1000,
    )
    await services.record(capture_run(run_id, body.text, reading))
    return CaptureResponse.of(reading)
