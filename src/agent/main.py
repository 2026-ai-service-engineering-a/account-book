"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

uvicorn agent.main:create_app --factory --port 8001
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from agent.application.ports import LanguageModel
from agent.application.use_cases import ReadCapture
from agent.infrastructure.llm import LitellmLanguageModel
from agent.infrastructure.settings import Settings
from agent.interfaces.services import Services
from agent.interfaces.web_app import build_web_app


def create_app(settings: Settings | None = None, model: LanguageModel | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if model is None:
        settings = settings or Settings()
        model = LitellmLanguageModel(
            settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
        )
    return build_web_app(Services(read_capture=ReadCapture(model)))
