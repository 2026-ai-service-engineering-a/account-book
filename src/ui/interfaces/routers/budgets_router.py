from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import BudgetStatus, Period
from ui.application.errors import LedgerValidationError
from ui.application.values import CategoryId, Money
from ui.interfaces.services import Services, ServicesDep
from ui.interfaces.templating import render

router = APIRouter()


@router.get("/budgets", response_class=HTMLResponse)
async def budgets_page(request: Request, services: ServicesDep) -> HTMLResponse:
    period = _period(services)
    statuses = await services.budgets.statuses(period)
    context = {
        "section": "budgets",
        "period": period,
        "statuses": statuses,
        "none_set": all(s.limit is None for s in statuses),
        "pace_notes": [s for s in statuses if s.over_on is not None],
    }
    return render(request, "budgets.html", context)


@router.get("/budgets/{category_id}", response_class=HTMLResponse)
async def budget_row(request: Request, services: ServicesDep, category_id: str) -> HTMLResponse:
    """취소 — 원래 값으로 되돌린다."""
    status = await services.budgets.status(CategoryId(category_id), _period(services))
    return _row(request, status)


@router.get("/budgets/{category_id}/edit", response_class=HTMLResponse)
async def budget_edit(request: Request, services: ServicesDep, category_id: str) -> HTMLResponse:
    status = await services.budgets.status(CategoryId(category_id), _period(services))
    value = f"{status.limit}" if status.limit is not None else ""
    return _edit_row(request, status, value, "")


@router.put("/budgets/{category_id}", response_class=HTMLResponse)
async def budget_save(
    request: Request,
    services: ServicesDep,
    category_id: str,
    amount: Annotated[str, Form()] = "",
    idempotency_key: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """줄 단위 저장이 곧 확인이다(budgets.md 4장). 실패하면 그 줄만 에러를 낸다."""
    digits = amount.replace(",", "").replace("원", "").strip()
    status = await services.budgets.status(CategoryId(category_id), _period(services))
    if digits and not digits.isdigit():
        return _edit_row(request, status, amount, "숫자로 넣어 주세요. 비우면 예산을 지웁니다.")
    try:
        saved = await services.budgets.set_limit(
            CategoryId(category_id), Money(int(digits)) if digits else None, idempotency_key
        )
    except LedgerValidationError as error:
        return _edit_row(request, status, amount, " ".join(error.details.values()))
    return _row(request, saved)


def _period(services: Services) -> Period:
    return Period.of(services.clock.now().date())


def _row(request: Request, status: BudgetStatus) -> HTMLResponse:
    return render(request, "partials/budget_row.html", {"status": status})


def _edit_row(request: Request, status: BudgetStatus, value: str, error: str) -> HTMLResponse:
    # 멱등성 키는 그 줄을 편집 상태로 바꿀 때 만든다
    context = {"status": status, "value": value, "error": error, "key": uuid.uuid4().hex}
    return render(request, "partials/budget_row_edit.html", context)
