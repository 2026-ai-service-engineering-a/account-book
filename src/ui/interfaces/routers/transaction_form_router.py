from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse

from ui.application.dto import Category, Direction, MessageReading, Period, Transaction
from ui.application.errors import LedgerValidationError
from ui.interfaces.forms.transaction_form import TransactionForm
from ui.interfaces.services import Services, ServicesDep
from ui.interfaces.templating import is_htmx, render

router = APIRouter()
_LAST_ACCOUNT = "last_account"
_READ_FIELDS = {"amount": "금액", "occurred_at": "날짜", "merchant": "가맹점"}
# 대역 모드에서 "예시 문자로 해보기"가 붙여넣는 문자. 이름과 카드 번호는 가렸다.
SAMPLE_MESSAGE = (
    "[Web발신]\n신한카드(1234)승인\n홍*동\n8,500원 일시불\n09/16 12:31 김밥천국\n누적1,234,500원"
)


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
    await _suggest_category(services, form, categories)
    context = {"form": form, "categories": categories, "errors": {}, "filled": frozenset()}
    return render(request, "partials/category_select.html", context)


@router.post("/partials/transaction-form/read", response_class=HTMLResponse)
async def read_card_message(request: Request, services: ServicesDep) -> HTMLResponse:
    """카드 문자를 붙여넣으면 폼 하나를 다시 그린다. 채우기까지만 — 저장은 사람이 누른다."""
    if services.reader is None:
        raise HTTPException(status_code=404)
    data = await request.form()
    form = TransactionForm.from_mapping(data)
    raw = data.get("card_message")
    message = raw.strip() if isinstance(raw, str) else ""
    if not message:
        return await _render_form(request, services, form, {}, None, note="붙여넣은 문자가 없어요.")
    reading = await services.reader.read(message, services.clock.now())
    filled = form.apply(reading, services.zone())
    if filled:
        categories = await services.catalog.categories(form.direction_value)
        if await _suggest_category(services, form, categories):
            filled |= {"category_id"}
    note = _reading_note(reading, filled)
    return await _render_form(
        request, services, form, {}, None, filled=filled, note=note, message=message
    )


async def _suggest_category(
    services: Services, form: TransactionForm, categories: tuple[Category, ...]
) -> bool:
    """제안은 비어 있을 때만 채운다. 사용자가 고른 것은 덮지 않는다(4.1). 채웠으면 True."""
    if form.category_id not in {c.id for c in categories}:
        form.category_id = ""
    if form.category_id or not form.merchant:
        return False
    suggestion = await services.suggester.suggest(form.merchant, form.direction_value)
    form.category_id = suggestion.category_id if suggestion else ""
    return suggestion is not None


def _reading_note(reading: MessageReading, filled: frozenset[str]) -> str:
    if not filled:
        return reading.refusal or "읽을 수 있는 내용이 없어요."
    missed = [name for key, name in _READ_FIELDS.items() if key not in filled]
    note = "문자를 읽어 표시한 칸을 채웠어요. 확인하고 저장하세요."
    return f"{note} 읽지 못한 칸: {', '.join(missed)}" if missed else note


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
    *,
    filled: frozenset[str] = frozenset(),
    note: str = "",
    message: str = "",
) -> HTMLResponse:
    """검증에 걸리면 폼 조각만 다시 그린다. 이미 쓴 값은 그대로 들어 있다."""
    context = {
        # 카드 문자 칸은 새로 넣을 때만. AI가 꺼져 있으면 칸이 없다(4.4).
        "reader_on": services.reader is not None and existing is None,
        "sample_message": SAMPLE_MESSAGE if services.demo is not None else "",
        "filled": filled,
        "reading_note": note,
        "card_message": message,
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
