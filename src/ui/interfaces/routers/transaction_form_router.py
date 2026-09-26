from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ui.application.dto import Direction, Period, Transaction
from ui.application.errors import LedgerValidationError
from ui.interfaces.forms.transaction_form import TransactionForm
from ui.interfaces.services import Services, ServicesDep
from ui.interfaces.templating import is_htmx, render

router = APIRouter()
_LAST_ACCOUNT = "last_account"


@router.get("/transactions/new", response_class=HTMLResponse)
async def new_form(request: Request, services: ServicesDep) -> HTMLResponse:
    # 결제수단 기본값은 마지막에 쓴 것(transaction-form.md 3장)
    account = request.cookies.get(_LAST_ACCOUNT, "card")
    form = TransactionForm.blank(services.clock.now(), account)
    return await _render_form(request, services, form, {}, None)


@router.post("/transactions")
async def create(request: Request, services: ServicesDep) -> Response:
    return await _save(request, services, None)


@router.get("/transactions/{transaction_id}", response_class=HTMLResponse)
async def edit_form(request: Request, services: ServicesDep, transaction_id: str) -> HTMLResponse:
    transaction = await services.transactions.get(transaction_id)
    form = TransactionForm.of(transaction, services.zone())
    return await _render_form(request, services, form, {}, transaction)


@router.post("/transactions/{transaction_id}")
async def update(request: Request, services: ServicesDep, transaction_id: str) -> Response:
    return await _save(request, services, await services.transactions.get(transaction_id))


@router.get("/transactions/{transaction_id}/delete", response_class=HTMLResponse)
async def delete_confirm(
    request: Request, services: ServicesDep, transaction_id: str
) -> HTMLResponse:
    """되돌릴 수 없으니 금액과 가맹점을 다시 보여 주고 묻는다(transaction-form.md 4.3)."""
    transaction = await services.transactions.get(transaction_id)
    names = {c.id: c.name for c in await services.catalog.categories()}
    context = {
        "section": "transactions",
        "transaction": transaction,
        "category_name": names.get(transaction.category_id, ""),
        "zone": services.zone(),
        "idempotency_key": uuid.uuid4().hex,
    }
    return render(request, "transaction_delete.html", context)


@router.post("/transactions/{transaction_id}/delete")
async def delete(
    services: ServicesDep, transaction_id: str, idempotency_key: Annotated[str, Form()]
) -> RedirectResponse:
    transaction = await services.transactions.get(transaction_id)
    await services.transactions.delete(transaction_id, idempotency_key)
    period = Period.of(transaction.occurred_at.astimezone(services.zone()).date())
    return RedirectResponse(f"/transactions?period={period}", status_code=303)


@router.get("/partials/category-select", response_class=HTMLResponse)
async def category_select(
    request: Request,
    services: ServicesDep,
    direction: str = "expense",
    category_id: str = "",
    merchant: str = "",
) -> HTMLResponse:
    """방향을 바꾸거나 가맹점을 넣으면 카테고리 셀렉트 하나만 갈아끼운다."""
    form = TransactionForm(direction=direction, category_id=category_id, merchant=merchant)
    categories = await services.catalog.categories(form.direction_value)
    if form.category_id not in {c.id for c in categories}:
        form.category_id = ""
    if not form.category_id and form.merchant:
        # 제안은 비어 있을 때만 채운다. 사용자가 고른 것은 덮지 않는다(4.1).
        suggestion = await services.suggester.suggest(form.merchant, form.direction_value)
        form.category_id = suggestion.category_id if suggestion else ""
    context = {"form": form, "categories": categories, "errors": {}}
    return render(request, "partials/category_select.html", context)


async def _save(request: Request, services: Services, existing: Transaction | None) -> Response:
    form = TransactionForm.from_mapping(await request.form())
    draft, errors = form.parse(services.zone())
    if draft is not None:
        try:
            if existing is None:
                saved = await services.transactions.create(draft, form.idempotency_key)
            else:
                saved = await services.transactions.update(existing.id, draft, form.idempotency_key)
        except LedgerValidationError as error:
            errors = error.details
        else:
            return _after_save(request, services, saved)
    return await _render_form(request, services, form, errors, existing)


def _after_save(request: Request, services: Services, saved: Transaction) -> Response:
    period = Period.of(saved.occurred_at.astimezone(services.zone()).date())
    url = f"/transactions?period={period}&saved={saved.id}"
    response: Response = (
        Response(status_code=204, headers={"HX-Redirect": url})
        if is_htmx(request)
        else RedirectResponse(url, status_code=303)
    )
    response.set_cookie(_LAST_ACCOUNT, saved.account_id, max_age=60 * 60 * 24 * 365, samesite="lax")
    return response


async def _render_form(
    request: Request,
    services: Services,
    form: TransactionForm,
    errors: dict[str, str],
    existing: Transaction | None,
) -> HTMLResponse:
    """검증에 걸리면 폼 조각만 다시 그린다. 이미 쓴 값은 그대로 들어 있다."""
    context = {
        "section": "new" if existing is None else "transactions",
        "form": form,
        "errors": errors,
        "existing": existing,
        "directions": (Direction.EXPENSE, Direction.INCOME),
        "categories": await services.catalog.categories(form.direction_value),
        "accounts": await services.catalog.accounts(),
    }
    name = "partials/transaction_form.html" if is_htmx(request) else "transaction_form.html"
    return render(request, name, context)
