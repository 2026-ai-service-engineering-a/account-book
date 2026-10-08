"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

uvicorn agent.main:create_app --factory --port 8001
"""

from __future__ import annotations

import logging
import time

from fastapi import FastAPI

from agent.application.dto import ClassifyThresholds, LoopLimits, RetrievalDefaults
from agent.application.ports import Embedder, LanguageModel, LedgerApi
from agent.application.use_cases import (
    AnswerQuestion,
    AskDocuments,
    ClassifyCategory,
    ReadCapture,
    Retrieve,
    SyncIndex,
)
from agent.domain.values import ChunkStrategy, SearchMode
from agent.infrastructure.http import HttpLedgerApi
from agent.infrastructure.llm import LitellmEmbedder, LitellmLanguageModel
from agent.infrastructure.settings import Settings
from agent.interfaces.services import Services
from agent.interfaces.web_app import build_web_app

# 테스트가 설정 없이 가짜만 끼울 때 쓰는 갈림길. 운영 값은 Settings가 낸다.
_DEFAULT_THRESHOLDS = ClassifyThresholds(min_confidence=0.7, abstain_below=0.25)
# 대화 한 번의 벽시계 상한. 흐름이 정하는 값이다(docs/ai/agent-loop.md 8장 — 대화 20초).
_CHAT_WALL_SECONDS = 20.0
_DEFAULT_LIMITS = LoopLimits(max_steps=8, max_cost_usd=0.5, wall_seconds=_CHAT_WALL_SECONDS)


def create_app(
    settings: Settings | None = None,
    model: LanguageModel | None = None,
    ledger: LedgerApi | None = None,
    embedder: Embedder | None = None,
) -> FastAPI:
    """가짜를 넘기면 그것을 쓰고, 넘기지 않은 자리는 설정으로 진짜를 만든다."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # litellm은 호출마다 INFO 두 줄을 찍는다. 우리 로그(capture done …)가 그 사이에 묻힌다.
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    thresholds, limits, defaults = _DEFAULT_THRESHOLDS, _DEFAULT_LIMITS, RetrievalDefaults()
    if model is None or ledger is None:
        settings = settings or Settings()
        thresholds = ClassifyThresholds(
            settings.classify_min_confidence, settings.classify_abstain_below
        )
        limits = LoopLimits(
            settings.agent_max_steps, settings.agent_max_cost_usd, _CHAT_WALL_SECONDS
        )
        defaults = RetrievalDefaults(
            ChunkStrategy(settings.doc_chunk_strategy),
            SearchMode(settings.doc_search_mode),
            settings.doc_top_k,
        )
        model = model or LitellmLanguageModel(
            settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
        )
        ledger = ledger or HttpLedgerApi(
            settings.api_base_url, timeout=settings.agent_timeout_seconds
        )
        if embedder is None and settings.embedding_model:
            embedder = LitellmEmbedder(
                settings.embedding_model,
                settings.api_key(settings.embedding_model),
                dimensions=settings.embedding_dimensions,
                timeout=settings.agent_timeout_seconds,
            )
    classify = ClassifyCategory(ledger, model, thresholds, embedder)
    answer = AnswerQuestion(model, ledger, limits, time.perf_counter)
    index = SyncIndex(ledger, embedder) if embedder else None
    retrieve = Retrieve(ledger, embedder, index, defaults)
    return build_web_app(
        Services(
            read_capture=ReadCapture(model, classify),
            classify=classify,
            answer=answer,
            retrieve=retrieve,
            ask=AskDocuments(retrieve, model),
        )
    )
