from __future__ import annotations

import asyncio
from datetime import date

from tests.ui.conftest import draft
from ui.application.dto import Direction, Period
from ui.infrastructure.memory import MemoryReportGateway, MemoryTransactionGateway


def _fill(store):
    gateway = MemoryTransactionGateway(store)
    rows = [
        draft(amount=150_000, month=8, day=5),
        draft(amount=100_000, day=2),
        draft(amount=82_300, day=16),
        draft(amount=31_000, day=3, category="cafe"),
        draft(amount=3_200_000, day=10, category="salary", direction=Direction.INCOME),
    ]
    for i, row in enumerate(rows):
        asyncio.run(gateway.create(row, f"k{i}"))


def test_monthly_compares_with_previous_month(store, clock):
    _fill(store)
    report = asyncio.run(MemoryReportGateway(store, clock).monthly(Period(2026, 9)))
    assert (report.totals.expense, report.totals.income) == (213_300, 3_200_000)
    food = report.by_category[0]
    assert (food.category.id, food.this_month, food.last_month) == ("food", 182_300, 150_000)
    assert (food.delta, food.percent) == (32_300, 22)
    assert report.through_day == 17
    assert [m.period for m in report.months] == [Period(2026, 8), Period(2026, 9)]


def test_first_month_has_no_comparison(store, clock):
    _fill(store)
    report = asyncio.run(MemoryReportGateway(store, clock).monthly(Period(2026, 8)))
    assert report.previous is None
    assert report.by_category[0].last_month is None
    assert report.through_day is None


def test_pace_needs_a_budget(store, clock):
    _fill(store)
    reports = MemoryReportGateway(store, clock)
    assert asyncio.run(reports.pace("food", Period(2026, 9))) is None
    store.limits["food"] = 300_000
    pace = asyncio.run(reports.pace("food", Period(2026, 9)))
    assert pace is not None
    assert len(pace.cumulative) == 17 and pace.cumulative[-1] == 182_300
    assert pace.projected == 321_705
    assert pace.over_on == date(2026, 9, 28)
