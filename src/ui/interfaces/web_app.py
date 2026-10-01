from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from ui.application.errors import LedgerUnavailable, TransactionNotFound

from .request_id import assign_request_id
from .routers import (
    budgets_router,
    category_select_router,
    chat_router,
    demo_router,
    reports_router,
    stand_in_api_router,
    transaction_form_router,
    transactions_router,
    wiki_router,
)
from .services import Services
from .templating import render

_STATIC = Path(__file__).parent / "static"


def build_web_app(services: Services) -> FastAPI:
    app = FastAPI(title="account-book ui", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = services
    app.middleware("http")(assign_request_id)
    app.mount("/static", StaticFiles(directory=_STATIC), name="static")
    for module in (
        chat_router,
        transactions_router,
        transaction_form_router,
        category_select_router,
        reports_router,
        budgets_router,
        demo_router,
        wiki_router,
    ):
        app.include_router(module.router)
    if services.index is not None:
        app.include_router(stand_in_api_router.router)
    app.add_exception_handler(TransactionNotFound, _not_found)
    app.add_exception_handler(LedgerUnavailable, _ledger_unavailable)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(Exception, _internal_error)
    return app


async def _not_found(request: Request, _: Exception) -> HTMLResponse:
    return _error(request, 404, "그 거래를 찾지 못했어요.")


async def _ledger_unavailable(request: Request, _: Exception) -> HTMLResponse:
    # api가 죽어도 화면은 멈추지 않고 무엇이 안 되는지 말한다. AI 자리는 각자 따로 폴백한다
    return _error(request, 503, "가계부 서버에 닿지 못했어요. 잠시 뒤에 다시 열어 주세요.")


async def _http_error(request: Request, error: Exception) -> HTMLResponse:
    status = error.status_code if isinstance(error, StarletteHTTPException) else 500
    return _error(
        request, status, "페이지를 찾지 못했어요." if status == 404 else "요청을 처리하지 못했어요."
    )


async def _internal_error(request: Request, _: Exception) -> HTMLResponse:
    # 500에는 내부 정보를 담지 않는다. 문의용 request_id만 보인다.
    return _error(request, 500, "문제가 생겼어요.")


def _error(request: Request, status: int, message: str) -> HTMLResponse:
    return render(request, "error.html", {"message": message, "status": status}, status_code=status)
