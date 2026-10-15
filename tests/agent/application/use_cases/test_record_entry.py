from __future__ import annotations

from datetime import datetime

from agent.application.use_cases.record_entry import entry_args, entry_of, proposal_run
from agent.domain.values import (
    CaptureReading,
    CategoryChoice,
    CategoryId,
    ChoiceStrategy,
    Direction,
    Money,
)
from tests.agent.conftest import SEOUL

NOW = datetime(2026, 10, 15, 12, tzinfo=SEOUL)


def test_income_without_a_category_falls_back_to_other_income_and_says_so():
    entry, unsure = entry_of(CaptureReading(direction=Direction.INCOME, amount=Money(100_000)), NOW)
    assert (entry.category_id, entry.occurred_at, unsure) == (
        "other_income",
        NOW,  # 말하지 않은 날짜는 지금
        ("category", "account"),
    )


def test_the_write_is_the_second_call_when_a_category_was_picked():
    choice = CategoryChoice(CategoryId("food"), ChoiceStrategy.HISTORY, "같은 가맹점")
    reading = CaptureReading(amount=Money(8500), merchant="김밥천국", category=choice)
    entry, _ = entry_of(reading, NOW)
    run = proposal_run("r1", "김밥천국 8500원", entry, choice)
    assert run.awaiting and run.stop_reason == "proposed"
    assert [(c.call_id, c.tool) for c in run.tool_calls] == [
        ("c1", "suggest_category"),
        ("c2", "create_transaction"),
    ]
    assert run.tool_calls[1].args == entry_args(entry) and "dry_run" not in entry_args(entry)
    alone = proposal_run("r2", "8500원", entry, None)
    assert [c.call_id for c in alone.tool_calls] == ["c1"]  # 고르지 않았으면 쓰기가 첫 호출
