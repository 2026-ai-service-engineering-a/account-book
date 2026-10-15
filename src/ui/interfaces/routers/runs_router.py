"""실행 기록 — AI가 한 일을 거슬러 본다(ui_docs/pages/runs.md). 읽기만 한다.

이 라우터에는 POST가 없다. 확인 대기인 제안도 여기서 확인하지 않는다 — 확인은 채팅의 카드가 한다.
`api`에 닿지 못하면 목록이나 펼친 자리에만 알리고 필터 바는 남긴다(5장).
"""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import RunFilter
from ui.application.errors import LedgerUnavailable
from ui.application.values import PageCursor, RunId
from ui.interfaces.presenters.run_view import SEATS, STATUSES
from ui.interfaces.services import Services, ServicesDep
from ui.interfaces.templating import render

router = APIRouter()


async def read_filter(seat: str = "", status: str = "") -> RunFilter:
    """모르는 값은 버린다 — 손으로 고친 URL에 422를 내지 않고 전부를 보인다."""
    return RunFilter(seat if seat in SEATS else "", status if status in STATUSES else "")


FilterDep = Annotated[RunFilter, Depends(read_filter)]


@router.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request, services: ServicesDep, criteria: FilterDep) -> HTMLResponse:
    context = await _list_context(services, criteria) | {"section": "runs"}
    return render(request, "runs.html", context)


@router.get("/partials/runs", response_class=HTMLResponse)
async def runs_results(
    request: Request, services: ServicesDep, criteria: FilterDep
) -> HTMLResponse:
    """필터를 바꾸면 #run-list 하나만 갈아끼운다. URL도 같이 바꾼다."""
    context = await _list_context(services, criteria)
    response = render(request, "partials/run_list.html", context)
    query = context["filter_query"]
    response.headers["HX-Push-Url"] = f"/runs?{query}" if query else "/runs"
    return response


@router.get("/partials/runs/more", response_class=HTMLResponse)
async def runs_more(
    request: Request, services: ServicesDep, criteria: FilterDep, cursor: str = ""
) -> HTMLResponse:
    context = await _list_context(services, criteria, PageCursor(cursor) if cursor else None)
    return render(request, "partials/run_rows.html", context)


@router.get("/partials/runs/{run_id}/calls", response_class=HTMLResponse)
async def run_calls(request: Request, services: ServicesDep, run_id: str) -> HTMLResponse:
    """행을 처음 펼칠 때 한 번 — 그 행의 도구 호출 자리만 채운다."""
    try:
        detail = await services.runs.get(RunId(run_id))
    except LedgerUnavailable:
        return render(request, "partials/run_calls.html", {"failed": True})
    context = {"detail": detail, "zone": services.zone(), "missing": detail is None}
    return render(request, "partials/run_calls.html", context)


@router.get("/runs/{run_id}", response_class=HTMLResponse)
async def run_page(request: Request, services: ServicesDep, run_id: str) -> HTMLResponse:
    """실행 하나를 펼친 채로 담은 한 장 — 거래 폼에서 오는 링크의 도착점이다."""
    detail = await services.runs.get(RunId(run_id))
    context = {"detail": detail, "zone": services.zone(), "section": "runs"}
    return render(request, "run.html", context, status_code=200 if detail else 404)


async def _list_context(
    services: Services, criteria: RunFilter, cursor: PageCursor | None = None
) -> dict[str, object]:
    query = urlencode(
        {k: v for k, v in (("seat", criteria.seat), ("status", criteria.status)) if v}
    )
    context: dict[str, object] = {
        "criteria": criteria,
        "filter_query": query,
        "zone": services.zone(),
        "page": None,
        "failed": False,
    }
    try:
        context["page"] = await services.runs.page(criteria, cursor)
    except LedgerUnavailable:
        context["failed"] = True
    return context
