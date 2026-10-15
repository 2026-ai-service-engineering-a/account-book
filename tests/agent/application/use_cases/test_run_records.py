from __future__ import annotations

import pytest

from agent.application.dto import (
    AnswerStatus,
    DocumentAnswer,
    LoopOutcome,
    ModelUsage,
    Retrieval,
    RunSeat,
    StopReason,
    ToolCall,
    ToolResult,
    ToolStep,
)
from agent.application.errors import LedgerRejected, LedgerUnavailable, ModelUnavailable
from agent.application.use_cases.read_capture import NO_AMOUNT, QUESTION
from agent.application.use_cases.run_records import (
    ask_run,
    capture_run,
    chat_run,
    classify_run,
    failed_run,
)
from agent.domain.values import (
    CaptureReading,
    CategoryChoice,
    CategoryId,
    ChoiceStrategy,
    Direction,
    Money,
    SearchMode,
)
from tests.agent.conftest import chunk

CAFE = CategoryChoice(
    CategoryId("cafe"), ChoiceStrategy.HISTORY, "같은 가맹점 최근 3건 중 3건: 카페"
)


def test_capture_with_a_merchant_leaves_the_category_pick_as_a_call():
    reading = CaptureReading(amount=Money(12345), merchant="블루보틀", category=CAFE)
    run = capture_run("r1", "블루보틀 12,345원", reading)
    assert (run.seat, run.stop_reason, run.utterance) == (
        RunSeat.CAPTURE,
        "read",
        "블루보틀 12,345원",
    )
    (call,) = run.tool_calls
    assert call.tool == "suggest_category" and call.args["direction"] == "expense"
    assert call.result == {"category_id": "cafe", "strategy": "history", "reason": CAFE.reason}


@pytest.mark.parametrize(("refusal", "stop"), [(QUESTION, "question"), (NO_AMOUNT, "no_amount")])
def test_capture_refusals_name_why(refusal, stop):
    run = capture_run("r1", "얼마 썼어?", CaptureReading.refused(refusal))
    assert run.stop_reason == stop and run.tool_calls == ()


def test_classify_stops_at_the_strategy_and_skips_the_call_without_input():
    run = classify_run("r1", "블루보틀", "라떼", Direction.EXPENSE, CAFE)
    assert run.utterance == "블루보틀\n라떼" and run.stop_reason == "history"
    empty = classify_run("r2", "", " ", Direction.EXPENSE, CategoryChoice.abstain("넣어 주세요"))
    assert empty.stop_reason == "none" and empty.tool_calls == ()


def test_chat_keeps_every_step_and_the_usage():
    call = ToolCall("call_1", "count_frequency", {"period": "last_week"})
    step = ToolStep(call, ToolResult("call_1", data={"count": 3}))
    outcome = LoopOutcome(StopReason.ANSWERED, "3번", (step, step), ModelUsage(100, 20, 0.0002), 3)
    run = chat_run("r1", "카페 몇 번?", outcome)
    assert (run.steps, run.tokens, run.cost_usd) == (3, 120, 0.0002)
    # 제공자가 같은 call_id를 다시 썼으면 순번을 붙여 감사 키를 지킨다
    assert [c.call_id for c in run.tool_calls] == ["call_1", "call_1#2"]
    assert run.tool_calls[0].result == {"call_id": "call_1", "ok": True, "data": {"count": 3}}


def test_ask_leaves_the_search_with_chunk_ids_only():
    found = chunk("8/1/1", "제8조", "철회할 수 있다")
    answer = DocumentAnswer(
        AnswerStatus.ANSWERED, "7일", (found,), Retrieval(SearchMode.HYBRID, False, (found,))
    )
    run = ask_run("r1", "노트북 취소", answer)
    assert run.stop_reason == "answered"
    assert run.tool_calls[0].result == {
        "fell_back": False,
        "chunk_ids": [found.id],
        "cited_ids": [found.id],
    }


@pytest.mark.parametrize(
    ("error", "stop"),
    [
        (ModelUnavailable("x"), "model_unavailable"),
        (LedgerRejected(404, "not_found", {}), "ledger_unavailable"),
        (LedgerUnavailable("x"), "ledger_unavailable"),
        (RuntimeError("x"), "internal_error"),
    ],
)
def test_failed_runs_name_where_they_could_not_reach(error, stop):
    run = failed_run("r1", RunSeat.CLASSIFY, "블루보틀", error)
    assert run.failed and run.stop_reason == stop
