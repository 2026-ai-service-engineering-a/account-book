from __future__ import annotations

from datetime import date, datetime

import pytest

from agent.application.dto import (
    LoopOutcome,
    ModelUsage,
    StopReason,
    ToolCall,
    ToolMeta,
    ToolResult,
    ToolStep,
)
from agent.application.use_cases.answer_text import (
    PARTIAL,
    UNAVAILABLE,
    UNCITED,
    UNVERIFIED,
    answer_text,
)
from agent.domain.tools import CategoryLine
from agent.domain.values import CategoryId, TimeRange
from tests.agent.conftest import SEOUL

TODAY = date(2026, 10, 8)
CATEGORIES = (CategoryLine(CategoryId("cafe"), "카페"), CategoryLine(CategoryId("food"), "식비"))


def span(m1: int, d1: int, m2: int, d2: int) -> TimeRange:
    return TimeRange(datetime(2026, m1, d1, tzinfo=SEOUL), datetime(2026, m2, d2, tzinfo=SEOUL))


def won(amount: int) -> dict[str, object]:
    return {"amount": amount, "currency": "KRW"}


def step(
    name: str, arguments: dict[str, object], data: dict[str, object], **periods: TimeRange
) -> ToolStep:
    meta = ToolMeta(1, False, 3, periods)
    return ToolStep(ToolCall("c1", name, arguments), ToolResult("c1", data, meta))


CAFE_WEEK = step(
    "count_frequency",
    {"period": "last_week", "category_id": "cafe"},
    {"count": 3, "day_count": 3, "avg_gap_days": 1.0, "avg_amount": won(5267)},
    period=span(9, 28, 10, 5),
)


def outcome(text: str, *steps: ToolStep, stop: StopReason = StopReason.ANSWERED) -> LoopOutcome:
    return LoopOutcome(stop, text, steps, ModelUsage(), 2, CATEGORIES)


def test_sentence_then_the_table_with_the_period_spelled_out():
    assert answer_text(outcome("저번 주에 카페에 3번 갔어요.", CAFE_WEEK), TODAY) == (
        "저번 주에 카페에 3번 갔어요.\n\n"
        "저번 주(9/28~10/4) · 카페\n"
        "3번 · 3일 · 평균 1일 간격 · 회당 5,267원"
    )


def test_an_invented_number_drops_the_sentence_but_keeps_the_table():
    text = answer_text(outcome("3번, 총 15,801원 썼어요.", CAFE_WEEK), TODAY)
    assert text.startswith("저번 주(9/28~10/4) · 카페") and "15,801" not in text


def test_zero_is_not_an_error():
    empty = step(
        "count_frequency",
        {"period": "last_week", "category_id": "cafe"},
        {"count": 0, "day_count": 0, "avg_gap_days": None, "avg_amount": None},
        period=span(9, 28, 10, 5),
    )
    assert answer_text(outcome("", empty), TODAY) == "저번 주(9/28~10/4) · 카페: 기록이 없어요"


def test_a_running_month_is_dated_up_to_today_and_merchants_are_quoted():
    month = step(
        "summarize_spending",
        {"period": "this_month", "merchant": "김밥천국"},
        {"expense": won(17_000), "income": won(0)},
        period=span(10, 1, 11, 1),
    )
    assert (
        answer_text(outcome("", month), TODAY) == "이번 달(10/1~10/8) · '김밥천국'\n지출 17,000원"
    )


def test_compare_shows_the_sign_and_the_aligned_ranges():
    compare = step(
        "compare_periods",
        {"a": "last_month", "b": "this_month", "category_id": "cafe"},
        {
            "changes": [
                {
                    "name": "카페",
                    "a": won(17_600),
                    "b": won(6_300),
                    "delta": won(-11_300),
                    "percent": 64,
                }
            ]
        },
        a=span(9, 1, 9, 9),
        b=span(10, 1, 11, 1),
    )
    text = answer_text(outcome("카페는 11,300원(64%) 줄었어요.", compare), TODAY)
    assert text == (
        "카페는 11,300원(64%) 줄었어요.\n\n"
        "지난달(9/1~9/8) → 이번 달(10/1~10/8)\n"
        "카페 17,600원 → 6,300원 (-11,300원, 64%)"
    )


def test_budget_lists_only_categories_with_a_budget():
    rows = [
        {"name": "식비", "spent": won(0), "limit": won(300_000), "percent": 0},
        {"name": "카페", "spent": won(6_300), "limit": None, "percent": None},
    ]
    budget = step(
        "get_budget_status", {"period": "this_month"}, {"budgets": rows}, period=span(10, 1, 11, 1)
    )
    assert (
        answer_text(outcome("", budget), TODAY)
        == "이번 달(10/1~10/8) 예산\n식비 0원 / 300,000원 (0%)"
    )


def test_search_lists_rows_in_the_users_dates_and_folds_the_rest():
    rows = [
        {"occurred_at": "2026-10-02T01:30:00+09:00", "merchant": "스타벅스", "amount": won(5_800)}
    ] * 7
    found = step(
        "search_transactions",
        {"period": "this_week"},
        {"transactions": rows, "has_more": False},
        period=span(10, 5, 10, 9),
    )
    lines = answer_text(outcome("", found), TODAY).split("\n")
    assert lines[0] == "이번 주(10/5~10/8)" and lines[1] == "10/2 스타벅스 5,800원"
    assert lines[-1] == "외 2개"


def test_a_cut_run_says_so_and_shows_what_it_has():
    text = answer_text(outcome("", CAFE_WEEK, stop=StopReason.MAX_STEPS), TODAY)
    assert text.startswith(PARTIAL + "\n\n저번 주(9/28~10/4)")


@pytest.mark.parametrize("stop", [StopReason.MODEL_UNAVAILABLE, StopReason.LEDGER_UNAVAILABLE])
def test_unreachable_providers(stop):
    assert answer_text(outcome("", stop=stop), TODAY) == UNAVAILABLE


def test_a_refusal_without_tools_passes_but_a_guess_does_not():
    assert (
        answer_text(outcome("다음 달 지출은 예측할 수 없어요."), TODAY)
        == "다음 달 지출은 예측할 수 없어요."
    )
    assert answer_text(outcome("다음 달엔 300,000원쯤 쓸 거예요."), TODAY) == UNVERIFIED


CHUNK = {
    "ref": "d4e5f60",
    "title": "조세특례제한법",
    "heading": "제126조의2 ② 2.",
    "effective_date": "2025-01-01",
    "body": "대중교통이용분의 100분의 40",
}
LAWS = step("search_documents", {"query": "대중교통 공제율"}, {"chunks": [CHUNK]})
TRANSPORT = step(
    "summarize_spending",
    {"period": "this_month", "category_id": "transport"},
    {"expense": won(52_000), "income": won(0)},
    period=span(10, 1, 11, 1),
)
SOURCE = "출처\n[1] 조세특례제한법 제126조의2 ② 2. · 시행 2025-01-01"


def test_a_cited_document_answer_gets_numbered_sources():
    text = answer_text(outcome("버스·지하철은 40%를 공제해요 [d4e5f60].", LAWS), TODAY)
    assert text == f"버스·지하철은 40%를 공제해요 [1].\n\n{SOURCE}"


def test_my_money_and_the_rate_side_by_side_pass():
    said = "이번 달 교통비는 52,000원이고, 대중교통은 40%를 공제해요 [d4e5f60]."
    text = answer_text(outcome(said, TRANSPORT, LAWS), TODAY)
    assert text.startswith("이번 달 교통비는 52,000원이고, 대중교통은 40%를 공제해요 [1].")
    assert text.endswith(SOURCE) and "이번 달(10/1~10/8)" in text


def test_the_multiplied_deduction_is_dropped():
    said = "52,000원의 40%인 20,800원을 공제받아요 [d4e5f60]."
    text = answer_text(outcome(said, TRANSPORT, LAWS), TODAY)
    assert "20,800" not in text and "20800" not in text
    assert text.startswith("이번 달(10/1~10/8)")  # 표와 찾은 조문만 남는다
    assert text.endswith("찾은 조문\n- 조세특례제한법 제126조의2 ② 2. · 시행 2025-01-01")


def test_a_rate_from_a_chunk_it_did_not_cite_is_dropped():
    text = answer_text(outcome("대중교통은 40%를 공제해요.", LAWS), TODAY)
    assert text.startswith(UNCITED) and "40%" not in text


def test_an_unknown_ref_is_dropped():
    text = answer_text(outcome("철회는 7일이에요 [d0000aa].", LAWS), TODAY)
    assert text.startswith(UNCITED)


def test_a_cut_run_still_shows_what_it_found():
    text = answer_text(outcome("", LAWS, stop=StopReason.MAX_STEPS), TODAY)
    assert text.startswith(PARTIAL) and "찾은 조문" in text
