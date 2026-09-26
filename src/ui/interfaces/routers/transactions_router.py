from __future__ import annotations

from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from ui.application.dto import Direction, Period, TransactionFilter
from ui.application.errors import TransactionNotFound
from ui.interfaces.services import Services, ServicesDep
from ui.interfaces.templating import render

router = APIRouter()
_RECENT_MONTHS = 12


async def read_filter(
    services: ServicesDep, period: str = "", direction: str = "", category: str = "", q: str = ""
) -> TransactionFilter:
    """필터는 URL 쿼리에 그대로 둔다. 기본은 이번 달(transactions.md 6장)."""
    current = Period.of(services.clock.now().date())
    return TransactionFilter(
        period=Period.parse(period) or current,
        direction=Direction(direction) if direction in {d.value for d in Direction} else None,
        category_id=category or None,
        query=q.strip(),
    )


FilterDep = Annotated[TransactionFilter, Depends(read_filter)]


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(
    request: Request, services: ServicesDep, criteria: FilterDep, saved: str = ""
) -> HTMLResponse:
    current = Period.of(services.clock.now().date())
    periods = [current]
    for _ in range(_RECENT_MONTHS - 1):
        periods.append(periods[-1].previous())
    context = await _list_context(services, criteria)
    context |= {
        "section": "transactions",
        "periods": periods,
        "notice": await _saved_notice(services, saved),
    }
    return render(request, "transactions.html", context)


@router.get("/partials/transactions", response_class=HTMLResponse)
async def transactions_results(
    request: Request, services: ServicesDep, criteria: FilterDep
) -> HTMLResponse:
    """필터를 바꾸면 #transaction-list와 #summary 둘만 갈아끼운다. URL도 같이 바꾼다."""
    context = await _list_context(services, criteria)
    response = render(request, "partials/transaction_results.html", context)
    query = context["filter_query"]
    response.headers["HX-Push-Url"] = f"/transactions?{query}" if query else "/transactions"
    return response


@router.get("/partials/transactions/more", response_class=HTMLResponse)
async def transactions_more(
    request: Request, services: ServicesDep, criteria: FilterDep, cursor: str = "", last: str = ""
) -> HTMLResponse:
    context = await _list_context(services, criteria, cursor or None)
    return render(request, "partials/transaction_rows.html", context | {"last_day": last})


async def _list_context(
    services: Services, criteria: TransactionFilter, cursor: str | None = None
) -> dict[str, object]:
    page = await services.transactions.search(criteria, cursor)
    categories = await services.catalog.categories()
    query = {
        "period": str(criteria.period),
        "direction": criteria.direction.value if criteria.direction else "",
        "category": criteria.category_id or "",
        "q": criteria.query,
    }
    return {
        "criteria": criteria,
        "page": page,
        "totals": await services.reports.totals(criteria),
        "has_any": bool(page.items) or await services.transactions.exists_any(),
        "categories": categories,
        "category_names": {c.id: c.name for c in categories},
        "filter_query": urlencode({k: v for k, v in query.items() if v}),
        "period_query": urlencode({"period": query["period"]}),
        "zone": services.zone(),
        "last_day": "",
    }


async def _saved_notice(services: Services, saved: str) -> dict[str, str] | None:
    """저장 뒤 목록 위의 한 줄. 예산을 넘겨도 막지 않고 알리기만 한다."""
    if not saved:
        return None
    try:
        transaction = await services.transactions.get(saved)
    except TransactionNotFound:
        return None
    if transaction.direction != Direction.EXPENSE:
        return {"kind": "ok", "text": "저장했어요."}
    period = Period.of(transaction.occurred_at.astimezone(services.zone()).date())
    status = await services.budgets.status(transaction.category_id, period)
    name = status.category.name
    if status.is_over and status.limit is not None:
        over = status.spent - status.limit
        return {"kind": "warn", "text": f"저장했어요. {name} 예산을 {over:,}원 넘었습니다."}
    if status.over_on is not None:
        when = f"{status.over_on.month}월 {status.over_on.day}일"
        return {"kind": "warn", "text": f"저장했어요. 이 페이스면 {when}에 {name} 예산을 넘습니다."}
    return {"kind": "ok", "text": "저장했어요."}
