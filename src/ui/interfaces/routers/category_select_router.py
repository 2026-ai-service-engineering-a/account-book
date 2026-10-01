"""거래 폼의 카테고리 셀렉트 한 칸. 갈아끼우는 길이 둘이다 — 방향을 바꿨을 때와 AI 버튼.

둘 다 셀렉트 partial 하나만 다시 그린다. 사용자가 이미 넣은 금액·날짜는 건드리지 않는다
(ui_docs/ui-design.md 5장).
"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ui.interfaces.forms.transaction_form import TransactionForm
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import render

router = APIRouter()


@router.get("/partials/category-select", response_class=HTMLResponse)
async def category_select(
    request: Request, services: ServicesDep, direction: str = "expense", category_id: str = ""
) -> HTMLResponse:
    """방향을 바꾸면 그 방향의 목록으로 갈아끼운다. 여기서는 고르지 않는다.

    고르는 것은 AI 버튼을 눌렀을 때뿐이다. 누르기 전에는 아무것도 부르지 않는다
    (docs/ai/category-suggestion-rag.md 8.1).
    """
    form = TransactionForm(direction=direction, category_id=category_id)
    categories = await services.catalog.categories(form.direction_value)
    form.drop_category_outside(categories)
    context = {"form": form, "categories": categories, "errors": {}, "filled": frozenset()}
    return render(request, "partials/category_select.html", context)


@router.post("/partials/category-suggest", response_class=HTMLResponse)
async def category_suggest(request: Request, services: ServicesDep) -> HTMLResponse:
    """카테고리 옆 AI 버튼. 가맹점·메모·방향을 보고 고른다.

    누른 것이 "바꿔도 된다"는 동의라서 이미 고른 값도 덮는다(category-suggestion-rag 10장).
    못 고르면 셀렉트는 그대로 두고 이유만 보여 준다(7장).
    """
    form = TransactionForm.from_mapping(await request.form())
    categories = await services.catalog.categories(form.direction_value)
    form.drop_category_outside(categories)
    suggestion = await services.suggester.suggest(form.merchant, form.memo, form.direction_value)
    context = {
        "form": form,
        "categories": categories,
        "errors": {},
        "filled": form.apply_suggestion(suggestion, categories, overwrite=True),
        "suggestion": suggestion,
    }
    return render(request, "partials/category_select.html", context)
