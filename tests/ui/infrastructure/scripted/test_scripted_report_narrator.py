from __future__ import annotations

import asyncio
from datetime import date

from ui.application.dto import (
    BudgetStatus,
    Category,
    CategoryChange,
    Direction,
    MonthlyReport,
    Period,
    Totals,
)
from ui.infrastructure.scripted import ScriptedReportNarrator

FOOD = Category("food", "식비", Direction.EXPENSE)
LIVING = Category("living", "생활", Direction.EXPENSE)
TRANSPORT = Category("transport", "교통", Direction.EXPENSE)


def test_picks_rises_pace_and_calm_budget():
    report = MonthlyReport(
        period=Period(2026, 9),
        totals=Totals(500_000, 0),
        previous=Totals(400_000, 0),
        by_category=(
            CategoryChange(FOOD, 182_300, 150_000, 32_300, 22),
            CategoryChange(LIVING, 318_000, 301_000, 17_000, 6),
        ),
        months=(),
        through_day=17,
    )
    budgets = (
        BudgetStatus(FOOD, 300_000, 182_300, 117_700, 60, 321_705, date(2026, 9, 28)),
        BudgetStatus(TRANSPORT, 100_000, 40_000, 60_000, 40, 70_000, None),
    )
    lines = asyncio.run(ScriptedReportNarrator().narrate(report, budgets))
    assert lines == (
        "식비가 지난달보다 32,300원 늘었어요.",
        "생활이 지난달보다 17,000원 늘었어요.",
        "식비 — 이 페이스면 9월 28일에 예산을 넘습니다.",
    )
