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
from ui.application.values import CategoryId, Money
from ui.infrastructure.scripted import ScriptedReportNarrator

FOOD = Category(CategoryId("food"), "식비", Direction.EXPENSE)
LIVING = Category(CategoryId("living"), "생활", Direction.EXPENSE)
TRANSPORT = Category(CategoryId("transport"), "교통", Direction.EXPENSE)


def test_picks_rises_pace_and_calm_budget():
    report = MonthlyReport(
        period=Period(2026, 9),
        totals=Totals(Money(500_000), Money(0)),
        previous=Totals(Money(400_000), Money(0)),
        by_category=(
            CategoryChange(FOOD, Money(182_300), Money(150_000), Money(32_300), 22),
            CategoryChange(LIVING, Money(318_000), Money(301_000), Money(17_000), 6),
        ),
        months=(),
        through_day=17,
    )
    budgets = (
        BudgetStatus(
            FOOD,
            Money(300_000),
            Money(182_300),
            Money(117_700),
            60,
            Money(321_705),
            date(2026, 9, 28),
        ),
        BudgetStatus(
            TRANSPORT, Money(100_000), Money(40_000), Money(60_000), 40, Money(70_000), None
        ),
    )
    lines = asyncio.run(ScriptedReportNarrator().narrate(report, budgets))
    assert lines == (
        "식비가 지난달보다 32,300원 늘었어요.",
        "생활이 지난달보다 17,000원 늘었어요.",
        "식비 — 이 페이스면 9월 28일에 예산을 넘습니다.",
    )
