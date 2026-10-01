from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from agent.interfaces.schemas import CategoryChoiceBody, ClassifyRequest
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/classify")
async def classify(body: ClassifyRequest, services: ServicesDep) -> CategoryChoiceBody:
    """카테고리를 고른다. 쓰지 않는다 — 셀렉트를 채우는 데까지만 쓰이고 저장은 사람이 한다."""
    started = time.perf_counter()
    choice = await services.classify(body.merchant, body.memo, body.direction_value())
    # 가맹점명은 남기지 않는다. 어느 길로 정해졌는지가 운영에 필요한 전부다(development-rules 6.4)
    _log.info(
        "classify done strategy=%s elapsed_ms=%d",
        choice.strategy.value,
        (time.perf_counter() - started) * 1000,
    )
    return CategoryChoiceBody.of(choice)
