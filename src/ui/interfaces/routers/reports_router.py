from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ui.application.dto import BudgetStatus, MonthlyReport, Period
from ui.interfaces.charts.category_bar_chart import CategoryBarChart
from ui.interfaces.charts.month_bar_chart import MonthBarChart
from ui.interfaces.charts.pace_chart import PaceChart
from ui.interfaces.services import ServicesDep
from ui.interfaces.templating import render

router = APIRouter()


@router.get("/reports")
async def reports_now(services: ServicesDep) -> RedirectResponse:
    return RedirectResponse(f"/reports/{Period.of(services.clock.now().date())}", status_code=307)


@router.get("/reports/{period_text}", response_class=HTMLResponse)
async def report_page(request: Request, services: ServicesDep, period_text: str) -> Response:
    period = Period.parse(period_text)
    if period is None:
        raise HTTPException(status_code=404)
    current = Period.of(services.clock.now().date())
    if period > current:  # 다음 달은 오늘이 속한 달까지만(reports.md 3장)
        return RedirectResponse(f"/reports/{current}", status_code=307)
    report = await services.reports.monthly(period)
    budgets = await services.budgets.statuses(period)
    target = _pace_target(budgets)
    pace = await services.reports.pace(target.category.id, period) if target else None
    context = {
        "section": "reports",
        "report": report,
        "current": current,
        "budgets": [b for b in budgets if b.limit is not None],
        "has_any": not report.is_empty or await services.transactions.exists_any(),
        "insights": await services.narrator.narrate(report, budgets) if not report.is_empty else (),
        "ask_url": "/?q=" + quote(_question(report)),
        "category_chart": CategoryBarChart.build(
            [(c.category.name, c.this_month) for c in report.by_category if c.this_month > 0]
        ),
        "pace_chart": PaceChart.build(pace) if pace else None,
        # 막대 하나뿐인 추이는 추이가 아니다 — 첫 달에는 통째로 감춘다
        "month_chart": MonthBarChart.build(report.months) if len(report.months) > 1 else None,
    }
    return render(request, "reports.html", context)


def _pace_target(budgets: tuple[BudgetStatus, ...]) -> BudgetStatus | None:
    """페이스 차트는 한 장. 넘는(넘은) 카테고리가 먼저, 없으면 가장 많이 쓴 비율."""
    budgeted = [b for b in budgets if b.limit is not None and b.spent > 0]
    if not budgeted:
        return None
    return max(budgeted, key=lambda b: (b.over_on is not None, b.percent or 0))


def _question(report: MonthlyReport) -> str:
    """리포트는 *무엇이*까지, *왜*는 대화가 답한다. 질문을 채운 채 채팅으로 넘긴다."""
    rises = [c for c in report.by_category if c.delta and c.delta > 0]
    if not rises:
        return f"{report.period.month}월 지출 어땠어?"
    top = max(rises, key=lambda c: c.delta or 0)
    return f"{report.period.month}월에 {top.category.name}가 왜 늘었어?"
