from __future__ import annotations

from datetime import date, datetime

from agent.application.dto import ToolCall, ToolError, ToolMeta, ToolResult, ToolStep
from agent.application.use_cases.number_check import numbers_from_tools, numbers_in, unsupported
from agent.domain.values import TimeRange
from tests.agent.conftest import SEOUL

WEEK = TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL))
TODAY = date(2026, 10, 8)
DATA = {
    "count": 7,
    "day_count": 5,
    "avg_gap_days": 1.4,
    "avg_amount": {"amount": 5200, "currency": "KRW"},
}
STEP = ToolStep(
    ToolCall("c1", "count_frequency", {"period": "last_week"}),
    ToolResult("c1", DATA, ToolMeta(1, False, 3, {"period": WEEK})),
)


def allowed() -> set[str]:
    return numbers_from_tools([STEP], TODAY)


def test_numbers_from_the_tool_pass_in_any_notation():
    assert unsupported("카페 7번, 5일, 평균 1.4일 간격에 회당 5,200원이에요.", allowed()) == []


def test_an_invented_total_is_caught():
    # 7번에 회당 5,200원이면 36,400원 — 맞든 틀리든 DB가 낸 값이 아니다(chat-analytics 7.2)
    assert unsupported("7번, 총 36,400원 썼네요.", allowed()) == ["36400"]


def test_dates_and_period_bounds_are_exempt():
    assert unsupported("저번 주(9/28~10/4)에 7번이에요. 오늘은 10월 8일.", allowed()) == []


def test_signs_are_dropped_so_a_decrease_can_be_told():
    data = {"delta": {"amount": -11300, "currency": "KRW"}, "percent": 64}
    step = ToolStep(ToolCall("c", "compare_periods", {}), ToolResult("c", data))
    assert unsupported("11,300원(64%) 줄었어요.", numbers_from_tools([step], TODAY)) == []


def test_failed_steps_lend_no_numbers():
    failed = ToolStep(STEP.call, ToolResult("c1", error=ToolError("not_found", False, "x")))
    assert unsupported("7번이에요.", numbers_from_tools([failed], TODAY)) == ["7"]


def test_numbers_in_a_text_see_fractions_as_their_parts():
    found = numbers_in("대중교통이용분 \N{MULTIPLICATION SIGN} 100분의 40, 연 250만원")
    assert {"100", "40", "250"} <= found
    assert unsupported("40%예요.", found) == []
