from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter

from agent.application.dto import RunSeat
from agent.application.errors import LedgerUnavailable, ModelUnavailable
from agent.application.use_cases.run_records import classify_run, failed_run
from agent.interfaces.schemas import CategoryChoiceBody, ClassifyRequest
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/classify")
async def classify(body: ClassifyRequest, services: ServicesDep) -> CategoryChoiceBody:
    """카테고리를 고른다. 쓰지 않는다 — 셀렉트를 채우는 데까지만 쓰이고 저장은 사람이 한다."""
    run_id = str(uuid.uuid4())
    started = time.perf_counter()
    direction = body.direction_value()
    try:
        choice = await services.classify(body.merchant, body.memo, direction)
    except (LedgerUnavailable, ModelUnavailable) as error:
        # 503도 실행이다 — 남기고 번역은 web_app의 처리기에 넘긴다
        utterance = "\n".join(part for part in (body.merchant, body.memo) if part.strip())
        await services.record(failed_run(run_id, RunSeat.CLASSIFY, utterance, error))
        raise
    # 가맹점명은 남기지 않는다. 어느 길로 정해졌는지가 운영에 필요한 전부다(development-rules 6.4)
    _log.info(
        "classify done run_id=%s strategy=%s elapsed_ms=%d",
        run_id,
        choice.strategy.value,
        (time.perf_counter() - started) * 1000,
    )
    await services.record(classify_run(run_id, body.merchant, body.memo, direction, choice))
    return CategoryChoiceBody.of(choice)
