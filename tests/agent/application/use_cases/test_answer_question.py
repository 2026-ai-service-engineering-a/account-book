from __future__ import annotations

import asyncio
import json
from datetime import date

import pytest

from agent.application.dto import (
    LoopEvent,
    LoopLimits,
    LoopOutcome,
    ModelReply,
    ModelUsage,
    StopReason,
    ToolCall,
)
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.use_cases import AnswerQuestion, Retrieve
from agent.domain.tools import READ_TOOLS, CategoryLine, Frequency, Mode, Permission
from agent.domain.values import Amount, CategoryId
from tests.agent.conftest import SEOUL, FakeLedger, FakeModel

TODAY = date(2026, 10, 8)
LIMITS = LoopLimits(max_steps=8, max_cost_usd=0.5, wall_seconds=20)
DICTIONARY = (CategoryLine(CategoryId("food"), "식비"), CategoryLine(CategoryId("cafe"), "카페"))
THREE = Frequency(3, 3, 1.0, Amount(5267))


def calls(*pairs: tuple[str, dict[str, object]], cost: float = 0.0) -> ModelReply:
    tool_calls = tuple(ToolCall(f"c{n}", name, args) for n, (name, args) in enumerate(pairs))
    return ModelReply("", tool_calls, ModelUsage(100, 10, cost))


def says(text: str) -> ModelReply:
    return ModelReply(text, (), ModelUsage(150, 20, 0.0))


def frequency(**args: object) -> tuple[str, dict[str, object]]:
    return ("count_frequency", {"period": "last_week", **args})


class Clock:
    def __init__(self, step: float = 0.01) -> None:
        self.now, self.step = 0.0, step

    def __call__(self) -> float:
        self.now += self.step
        return self.now


def ask(
    tape: list[ModelReply | Exception],
    ledger: FakeLedger | None = None,
    limits: LoopLimits = LIMITS,
    clock: Clock | None = None,
) -> tuple[list[LoopEvent], LoopOutcome, FakeModel, FakeLedger]:
    model = FakeModel(tape=tape)
    ledger = ledger or FakeLedger(replies={"categories": DICTIONARY, "frequency": THREE})
    pauses: list[float] = []

    async def pause(seconds: float) -> None:
        pauses.append(seconds)

    loop = AnswerQuestion(
        model, ledger, Retrieve(ledger, None, None), limits, clock or Clock(), pause
    )

    async def go() -> list[LoopEvent]:
        return [e async for e in loop("저번 주에 카페 몇 번 갔어?", TODAY, SEOUL)]

    events = asyncio.run(go())
    outcome = events[-1].outcome
    assert outcome is not None
    return events, outcome, model, ledger


def test_pick_a_tool_read_the_result_answer():
    events, outcome, model, _ = ask([calls(frequency(category_id="cafe")), says("3번이에요.")])
    assert [e.tool for e in events[:-1]] == ["count_frequency"]
    assert (outcome.stop, outcome.text) == (StopReason.ANSWERED, "3번이에요.")
    assert outcome.model_calls == 2
    (step,) = outcome.steps
    assert step.result.ok and step.result.data == {
        "count": 3,
        "day_count": 3,
        "avg_gap_days": 1.0,
        "avg_amount": {"amount": 5267, "currency": "KRW"},
    }
    first, second = model.tool_prompts
    assert "2026-10-08 (목)" in first.turns[0].text and "<<<DATA" in first.turns[0].text
    assert [t.role for t in second.turns] == ["user", "assistant", "tool"]
    assert json.loads(second.turns[2].text)["call_id"] == "c0"
    assert outcome.usage == ModelUsage(250, 30, 0.0)


def test_only_read_tools_are_offered():
    _, _, model, _ = ask([says("못 해요.")])
    offered = [s.name for s in model.tool_prompts[0].tools]
    assert offered == list(Mode.QUERY.tools)
    assert all(name in READ_TOOLS and name.permission is Permission.READ for name in offered)


def test_step_limit_stops_with_what_was_gathered():
    limits = LoopLimits(max_steps=2, max_cost_usd=0.5, wall_seconds=20)
    tape: list[ModelReply | Exception] = [
        calls(frequency(category_id="cafe")),
        calls(frequency(category_id="food")),
        says("never"),
    ]
    _, outcome, _, _ = ask(tape, limits=limits)
    assert outcome.stop is StopReason.MAX_STEPS and len(outcome.steps) == 2 and outcome.text == ""


def test_cost_limit_is_checked_before_the_next_step():
    _, outcome, model, _ = ask([calls(frequency(), cost=0.6), says("never")])
    assert outcome.stop is StopReason.MAX_COST and len(model.tool_prompts) == 1


def test_wall_clock_limit():
    _, outcome, model, _ = ask([says("never")], clock=Clock(step=30))
    assert outcome.stop is StopReason.WALL_CLOCK and model.tool_prompts == []


def test_the_same_call_twice_is_cut():
    _, outcome, _, ledger = ask([calls(frequency()), calls(frequency()), says("never")])
    assert outcome.stop is StopReason.REPEATED
    assert len([c for c in ledger.calls if c[0] == "frequency"]) == 1


def test_a_category_name_becomes_its_id_and_an_unknown_word_becomes_a_merchant():
    tape: list[ModelReply | Exception] = [
        calls(frequency(category_id="카페"), frequency(category_id="커피")),
        says("끝"),
    ]
    _, _, _, ledger = ask(tape)
    filters = [args[0] for name, args in ledger.calls if name == "frequency"]
    assert [(f.category_id, f.text) for f in filters] == [("cafe", ""), (None, "커피")]  # type: ignore[attr-defined]


def test_an_unknown_category_where_no_merchant_fits_is_sent_back_without_calling_the_api():
    compare: tuple[str, dict[str, object]] = (
        "compare_periods",
        {"a": "last_month", "b": "this_month", "category_id": "커피"},
    )
    _, outcome, _, ledger = ask([calls(compare), says("끝")])
    result = outcome.steps[0].result
    assert result.error is not None and "food, cafe" in result.error.hint
    assert [c[0] for c in ledger.calls] == ["categories"]


def test_three_bad_tries_at_one_tool_stop_the_run():
    bad = [calls(("count_frequency", {"period": f"bad{n}"})) for n in range(3)]
    _, outcome, _, _ = ask([*bad, says("never")])
    assert outcome.stop is StopReason.TOOL_FAILED and len(outcome.steps) == 3


def test_server_errors_are_retried_by_code_without_spending_steps():
    ledger = FakeLedger(
        replies={"categories": DICTIONARY, "frequency": LedgerUnavailable("HTTP 500")}
    )
    _, outcome, _, _ = ask([calls(frequency()), says("못 봤어요.")], ledger=ledger)
    assert len([c for c in ledger.calls if c[0] == "frequency"]) == 3  # 처음 + 두 번
    assert outcome.model_calls == 2 and outcome.steps[0].result.error is not None


def test_malformed_output_is_asked_again_once():
    _, outcome, _, _ = ask([MalformedOutput("x"), says("3번이에요.")])
    assert outcome.stop is StopReason.ANSWERED
    _, outcome, _, _ = ask([MalformedOutput("x"), MalformedOutput("y"), says("never")])
    assert outcome.stop is StopReason.MALFORMED


@pytest.mark.parametrize(
    ("ledger_down", "tape", "stop"),
    [
        (False, [calls(frequency()), ModelUnavailable("down")], StopReason.MODEL_UNAVAILABLE),
        (True, [says("never")], StopReason.LEDGER_UNAVAILABLE),
    ],
)
def test_unreachable_providers_end_the_run(ledger_down, tape, stop):
    replies: dict[str, object] = {"categories": DICTIONARY, "frequency": THREE}
    if ledger_down:
        replies["categories"] = LedgerUnavailable("ConnectError")
    _, outcome, _, _ = ask(tape, ledger=FakeLedger(replies=replies))
    assert outcome.stop is stop
