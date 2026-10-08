from __future__ import annotations

import logging
import time

from fastapi import APIRouter

from agent.interfaces.schemas import AskRequest, AskResponse
from agent.interfaces.services import ServicesDep

router = APIRouter()
_log = logging.getLogger(__name__)


@router.post("/ask")
async def ask(body: AskRequest, services: ServicesDep) -> AskResponse:
    """문서 Q&A. 실패해도 200이다 — 찾은 조각만 보이는 답(search_only)으로 떨어진다."""
    started = time.perf_counter()
    found = await services.ask(body.q)
    # 질문과 답은 남기지 않는다(development-rules 6.4)
    _log.info(
        "ask done status=%s elapsed_ms=%d",
        found.status.value,
        (time.perf_counter() - started) * 1000,
    )
    return AskResponse.of(found)
