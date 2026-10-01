from __future__ import annotations

from fastapi import FastAPI

from .error_translation import install_error_translation
from .routers import catalog_router, health_router, transactions_router
from .services import Services


def build_web_app(services: Services) -> FastAPI:
    # 헤드리스다. 계약의 정본은 docs/api-contract.md라 문서 페이지를 열지 않는다.
    app = FastAPI(title="account-book api", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = services
    for module in (health_router, transactions_router, catalog_router):
        app.include_router(module.router)
    install_error_translation(app)
    return app
