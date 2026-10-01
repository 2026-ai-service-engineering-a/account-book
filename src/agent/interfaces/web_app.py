from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent.application.errors import LedgerUnavailable, ModelUnavailable

from .routers import capture_router, classify_router, health_router
from .schemas import ErrorResponse
from .services import Services

_log = logging.getLogger(__name__)


def build_web_app(services: Services) -> FastAPI:
    # 헤드리스다. ui만 부르고, 계약은 화면 문서가 정본이라 문서 페이지를 열지 않는다.
    app = FastAPI(title="account-book agent", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = services
    for module in (capture_router, classify_router, health_router):
        app.include_router(module.router)
    app.add_exception_handler(ModelUnavailable, _model_unavailable)
    app.add_exception_handler(LedgerUnavailable, _ledger_unavailable)
    return app


async def _model_unavailable(_: Request, error: Exception) -> JSONResponse:
    # 처리하는 곳에서 한 번만 남긴다. 예외 이름만 — 메시지에 키가 섞여 나올 수 있다.
    _log.warning("model unavailable: %s", error)
    body = ErrorResponse.of("model_unavailable", "지금은 AI를 부를 수 없어요.")
    return JSONResponse(body.model_dump(), status_code=503)


async def _ledger_unavailable(_: Request, error: Exception) -> JSONResponse:
    _log.warning("ledger unavailable: %s", error)
    body = ErrorResponse.of("ledger_unavailable", "지금은 가계부 기록을 찾아볼 수 없어요.")
    return JSONResponse(body.model_dump(), status_code=503)
