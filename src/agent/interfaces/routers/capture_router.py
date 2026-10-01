from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from agent.interfaces.schemas import CaptureRequest, CaptureResponse
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/capture")
async def capture(body: CaptureRequest, services: ServicesDep) -> CaptureResponse:
    """한 줄을 거래 칸으로 읽는다. 쓰지 않는다 — 저장은 ui의 폼이 사람 손으로 한다."""
    started = time.perf_counter()
    reading = await services.read_capture(body.text, body.local_now())
    # 운영 로그에는 원문·금액·가맹점을 남기지 않는다(development-rules 6.4)
    _log.info(
        "capture done refused=%s elapsed_ms=%d",
        bool(reading.refusal),
        (time.perf_counter() - started) * 1000,
    )
    return CaptureResponse.of(reading)
