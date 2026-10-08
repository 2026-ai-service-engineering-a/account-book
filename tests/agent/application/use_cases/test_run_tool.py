from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime

import pytest

from agent.application.dto import ToolCall, ToolResult, TransactionFilter
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.application.use_cases import Retrieve, RunTool
from agent.domain.tools import (
    READ_TOOLS,
    CategoryShift,
    DocumentLine,
    Frequency,
    SpendingTotals,
    TransactionLine,
    TransactionList,
)
from agent.domain.values import Amount, CategoryId, Direction, TimeRange
from tests.agent.conftest import SEOUL, FakeEmbedder, FakeLedger, chunk, evidence, search

TODAY = date(2026, 10, 8)  # 목요일
FREQUENCY = Frequency(3, 3, 1.0, Amount(5267))
REFUSED = LedgerRejected(422, "validation_error", {"category_id": "없음"})


def at(month: int, day: int) -> datetime:
    return datetime(2026, month, day, tzinfo=SEOUL)


class Ticks:
    """부를 때마다 0.038초씩 가는 시계."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        self.now += 0.038
        return self.now


def run(ledger: FakeLedger, name: str, **arguments: object) -> ToolResult:
    tool = RunTool(ledger, Retrieve(ledger, FakeEmbedder(), None), READ_TOOLS, Ticks())
    return asyncio.run(tool(ToolCall("call_1", name, arguments), TODAY, SEOUL))


def test_last_week_cafe_resolves_the_period_and_calls_the_api_once():
    ledger = FakeLedger(replies={"frequency": FREQUENCY})
    result = run(ledger, "count_frequency", period={"name": "last_week"}, category_id="cafe")
    week = TimeRange(at(9, 28), at(10, 5))
    assert ledger.calls == [
        ("frequency", (TransactionFilter(week, CategoryId("cafe"), "", Direction.EXPENSE),))
    ]
    assert result.envelope() == {
        "call_id": "call_1",
        "ok": True,
        "data": {
            "count": 3,
            "day_count": 3,
            "avg_gap_days": 1.0,
            "avg_amount": {"amount": 5267, "currency": "KRW"},
        },
        "meta": {
            "row_count": 1,
            "truncated": False,
            "elapsed_ms": 38,
            "periods": {
                "period": {"from": "2026-09-28T00:00:00+09:00", "to": "2026-10-05T00:00:00+09:00"}
            },
        },
    }


def test_a_tool_outside_the_seat_is_refused_without_calling_the_api():
    ledger = FakeLedger()
    tool = RunTool(ledger, Retrieve(ledger, None, None), set(READ_TOOLS), Ticks())
    call = ToolCall("call_9", "delete_transaction", {"transaction_id": "t1"})
    result = asyncio.run(tool(call, TODAY, SEOUL))
    assert result.error is not None and result.error.code == "validation_error"
    assert not result.error.retryable and ledger.calls == []


def test_bad_arguments_come_back_as_a_retryable_envelope():
    ledger = FakeLedger()
    result = run(ledger, "count_frequency", period={"name": "lastweek"})
    assert result.error is not None
    assert (result.error.code, result.error.retryable) == ("validation_error", True)
    assert result.error.hint.startswith("period:") and ledger.calls == []


@pytest.mark.parametrize(
    ("raised", "code", "retryable"),
    [
        (REFUSED, "validation_error", True),
        (LedgerRejected(404, "not_found", {}), "not_found", False),
        (LedgerUnavailable("ConnectError"), "internal_error", True),
    ],
)  # fmt: skip
def test_api_failures_follow_the_table_and_are_not_retried(raised, code, retryable):
    ledger = FakeLedger(replies={"summary": raised})
    result = run(ledger, "summarize_spending", period="this_month")
    assert result.error is not None
    assert (result.error.code, result.error.retryable) == (code, retryable)
    assert len(ledger.calls) == 1  # 재시도는 루프의 일이다
    if code == "validation_error":
        assert "category_id: 없음" in result.error.hint  # api의 message가 아니라 우리 문장


def test_search_shows_times_in_the_users_zone_and_says_when_there_is_more():
    line = TransactionLine(
        "t1",
        datetime(2026, 10, 1, 16, 30, tzinfo=UTC),  # 서울로는 10/2 01:30
        Direction.EXPENSE,
        Amount(5800),
        CategoryId("cafe"),
        "스타벅스",
        "",
    )
    ledger = FakeLedger(replies={"transactions": TransactionList((line,), has_more=True)})
    result = run(ledger, "search_transactions", period="this_week")
    assert ledger.calls[0][1][1] == 20  # 기본 20건
    assert result.data is not None
    assert result.data["transactions"][0]["occurred_at"] == "2026-10-02T01:30:00+09:00"  # type: ignore[index]
    assert result.meta is not None and result.meta.truncated
    assert "좁혀라" in result.meta.note


def test_big_pages_are_cut_to_eight_kilobytes():
    line = TransactionLine(
        "t", at(10, 1), Direction.EXPENSE, Amount(1), CategoryId("food"), "가" * 100, "나" * 100
    )
    ledger = FakeLedger(replies={"transactions": TransactionList((line,) * 50, has_more=False)})
    result = run(ledger, "search_transactions", period="this_month", limit=50)
    assert result.meta is not None and result.meta.truncated
    assert 0 < result.meta.row_count < 50


def test_compare_cuts_last_month_to_the_days_this_month_has_had():
    ledger = FakeLedger(replies={"compare": ()})
    result = run(ledger, "compare_periods", a="last_month", b="this_month")
    a, b, _ = ledger.calls[0][1]
    assert a == TimeRange(at(9, 1), at(9, 9))  # 9/1~9/8 — 10/1~10/8과 같은 여드레
    assert b == TimeRange(at(10, 1), at(11, 1))
    assert result.meta is not None and "8일" in result.meta.note


def test_compare_of_two_finished_periods_is_left_alone():
    shift = CategoryShift(CategoryId("cafe"), "카페", Amount(0), Amount(6300), Amount(6300), None)
    ledger = FakeLedger(replies={"compare": (shift,)})
    result = run(ledger, "compare_periods", a={"name": "month", "month": "2026-08"}, b="last_month")
    a, _, _ = ledger.calls[0][1]
    assert a == TimeRange(at(8, 1), at(9, 1))
    assert result.meta is not None and result.meta.note == "" and result.meta.row_count == 1


def test_budget_is_asked_by_month():
    ledger = FakeLedger(replies={"budget_status": ()})
    assert run(ledger, "get_budget_status", period="this_month").ok
    assert ledger.calls == [("budget_status", (date(2026, 10, 1), None))]
    assert not run(ledger, "get_budget_status", period="this_week").ok


def test_summary_is_two_sums():
    ledger = FakeLedger(replies={"summary": SpendingTotals(Amount(457_700), Amount(0))})
    result = run(ledger, "summarize_spending", period="this_month")
    assert result.data == {
        "expense": {"amount": 457700, "currency": "KRW"},
        "income": {"amount": 0, "currency": "KRW"},
    }


def test_suggest_never_sends_a_vector_and_keeps_eight_pieces_of_evidence():
    many = tuple(evidence(f"t{n}", "스타벅스", "cafe", 0.7) for n in range(12))
    ledger = FakeLedger(search(found=many))
    result = run(ledger, "suggest_category", merchant="블루보틀")
    (query,) = ledger.queries
    assert query.embedding_model == "" and query.query_vector is None  # 임베딩도 모델 호출이다
    assert result.data is not None and len(result.data["evidence"]) == 8  # type: ignore[arg-type]
    assert result.data["candidates"][0] == {"category_id": "cafe", "confidence": 0.9}  # type: ignore[index]


WITHDRAW = chunk("8/1/1", "제8조 ① 1.", "계약서를 받은 날부터 7일")


def test_documents_are_found_like_retrieve_and_cited_by_short_refs():
    ledger = FakeLedger(replies={"search_documents": (WITHDRAW,)})
    result = run(ledger, "search_documents", query="할부 철회 기간")
    (query,) = ledger.calls[0][1]
    assert query.text == "할부 철회 기간"  # type: ignore[attr-defined]
    assert query.query_vector == (8.0, 1.0)  # type: ignore[attr-defined]  # /retrieve처럼 임베딩
    assert result.data == {
        "chunks": [
            {
                "ref": DocumentLine.ref_for(WITHDRAW.id),
                "title": "할부거래에 관한 법률",
                "heading": "제8조 ① 1.",
                "effective_date": "2025-01-01",
                "body": WITHDRAW.body,
            }
        ]
    }
    assert result.meta is not None and result.meta.row_count == 1 and result.meta.note == ""


def test_documents_say_when_the_vector_search_fell_back_to_words():
    ledger = FakeLedger(replies={"search_documents": (WITHDRAW,)})
    tool = RunTool(ledger, Retrieve(ledger, FakeEmbedder(fail=True), None), READ_TOOLS, Ticks())
    call = ToolCall("call_1", "search_documents", {"query": "할부 철회"})
    result = asyncio.run(tool(call, TODAY, SEOUL))
    assert result.meta is not None and "낱말로만" in result.meta.note


def test_long_documents_are_cut_to_eight_kilobytes():
    long = [chunk(f"8/{n}", f"제8조 {n}", "가" * 900) for n in range(8)]
    ledger = FakeLedger(replies={"search_documents": tuple(long)})
    result = run(ledger, "search_documents", query="할부")
    assert result.meta is not None and result.meta.truncated
    assert 0 < result.meta.row_count < 8 and "조각까지만" in result.meta.note
