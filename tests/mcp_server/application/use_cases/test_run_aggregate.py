from __future__ import annotations

import asyncio
from datetime import date

from mcp_server.application.dto import LedgerFilter
from mcp_server.application.parsers import parse_arguments
from mcp_server.application.use_cases import RunAggregate
from mcp_server.domain.tools import ToolName
from mcp_server.domain.values import TimeRange
from tests.mcp_server.conftest import NOW, SEOUL, FakeLedger


def run(ledger: FakeLedger, name: ToolName, arguments: dict[str, object]):
    request = parse_arguments(name, arguments)
    return asyncio.run(RunAggregate(ledger)(request, NOW.date(), SEOUL))


def test_summing_resolves_the_period_in_the_users_zone():
    ledger = FakeLedger()
    data, meta = run(
        ledger, ToolName.SUMMARIZE_SPENDING, {"period": "last_week", "merchant": "카페"}
    )
    where = ledger.seen[0]
    assert isinstance(where, LedgerFilter) and where.text == "카페"
    assert data["expense"] == {"amount": 412000, "currency": "KRW"}
    assert meta["periods"] == {
        "period": {"from": "2026-10-05T00:00:00+09:00", "to": "2026-10-12T00:00:00+09:00"}
    }
    assert meta["row_count"] == 1 and meta["truncated"] is False


def test_the_budget_is_read_for_the_month_the_period_starts_in():
    ledger = FakeLedger()
    data, _ = run(ledger, ToolName.GET_BUDGET_STATUS, {"period": "last_month"})
    assert ledger.seen == [(date(2026, 9, 1), "")]
    assert data["budgets"][0]["name"] == "식비"


def test_a_month_in_progress_is_compared_with_the_same_number_of_days():
    ledger = FakeLedger()
    _, meta = run(ledger, ToolName.COMPARE_PERIODS, {"a": "last_month", "b": "this_month"})
    found = ledger.seen[0]
    assert isinstance(found, tuple)
    a, b, _ = found
    assert isinstance(a, TimeRange) and isinstance(b, TimeRange)
    assert (a.end.date(), b.end.date()) == (date(2026, 9, 16), date(2026, 11, 1))
    assert "15일" in str(meta["note"])


def test_more_than_thirty_changes_are_cut_and_said_so():
    arguments: dict[str, object] = {"a": "last_month", "b": "last_week"}
    data, meta = run(FakeLedger(changes=40), ToolName.COMPARE_PERIODS, arguments)
    assert len(data["changes"]) == 30
    assert meta["truncated"] is True and "30줄까지만" in str(meta["note"])
