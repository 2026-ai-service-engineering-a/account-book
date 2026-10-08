from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from agent.domain.values import ChunkStrategy, SearchMode
from agent.interfaces.schemas import RetrieveRequest, RetrieveResponse
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/retrieve")
async def retrieve(body: RetrieveRequest, services: ServicesDep) -> RetrieveResponse:
    """문서 조각을 찾는다 — 질문을 임베딩해 api에 묻는다. 생성 모델은 부르지 않는다."""
    started = time.perf_counter()
    found = await services.retrieve(
        body.q, ChunkStrategy(body.strategy), body.k, SearchMode(body.mode)
    )
    # 질문 원문은 남기지 않는다(development-rules 6.4)
    _log.info(
        "retrieve done mode=%s fell_back=%s chunks=%d elapsed_ms=%d",
        found.mode.value,
        found.fell_back,
        len(found.chunks),
        (time.perf_counter() - started) * 1000,
    )
    return RetrieveResponse.of(found)
