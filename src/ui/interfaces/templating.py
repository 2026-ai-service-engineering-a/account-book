from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .ai_map import BY_KEY
from .presenters.money_format import change, grouped, signed_won, won
from .request_id import request_id_of

_TEMPLATES = Path(__file__).parent / "templates"


def _page_context(request: Request) -> dict[str, object]:
    services = getattr(request.app.state, "services", None)
    return {
        "demo": getattr(services, "demo", None) is not None,
        "request_id": request_id_of(request),
    }


templates = Jinja2Templates(directory=_TEMPLATES, context_processors=[_page_context])
templates.env.filters.update(won=won, signed=signed_won, grouped=grouped, change=change)
# 화면의 AI 표시가 읽는 자리 목록. 위키도 같은 것을 읽는다.
templates.env.globals["AI_SEATS"] = BY_KEY


def render(
    request: Request,
    name: str,
    context: Mapping[str, object] | None = None,
    status_code: int = 200,
) -> HTMLResponse:
    return templates.TemplateResponse(request, name, dict(context or {}), status_code=status_code)


def fragment(name: str, context: Mapping[str, object]) -> str:
    """SSE에 실어 보낼 HTML 조각. 요청 문맥 없이 그린다."""
    return templates.get_template(name).render(context)


def is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"
