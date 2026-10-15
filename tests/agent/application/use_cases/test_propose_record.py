from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from agent.application.dto import ClassifyThresholds, RecordReply
from agent.application.errors import LedgerUnavailable
from agent.application.use_cases import ClassifyCategory, ProposeRecord, ReadCapture, RecordRun
from agent.domain.tools import CategoryLine, TransactionLine
from agent.domain.values import Amount, CategoryId, Direction
from tests.agent.conftest import SEOUL, FakeLedger, FakeModel, extraction, search
from tests.agent.fake_audit import FakeAuditTable

NOW = datetime(2026, 10, 15, 12, tzinfo=SEOUL)
SAID = "어제 점심 김밥천국 8500원 카드로"
NAMES = (CategoryLine(CategoryId("food"), "식비"), CategoryLine(CategoryId("etc"), "기타"))
CREATED = TransactionLine(
    "t1", datetime(2026, 10, 14, 3, 30, tzinfo=UTC), Direction.EXPENSE, Amount(8500),
    CategoryId("food"), "김밥천국", "",
)  # fmt: skip


def lunch(**overrides: object) -> dict[str, object]:
    return (
        extraction(
            amount=8500, merchant="김밥천국", payment="card", day="yesterday", hour=12, minute=30
        )
        | overrides
    )


def ledger(*searches: object, **replies: object) -> FakeLedger:
    base: dict[str, object] = {"categories": NAMES, "create_transaction": CREATED}
    found = searches or (search(candidates=(("food", 0.9),)),)
    return FakeLedger(*found, replies=base | replies)  # type: ignore[arg-type]


def proposer(model: FakeModel, found: FakeLedger, table: FakeAuditTable) -> ProposeRecord:
    classify = ClassifyCategory(found, model, ClassifyThresholds(0.7, 0.25))
    ids = iter(f"run-{n}" for n in range(1, 10))
    return ProposeRecord(
        ReadCapture(model, classify), found, table, RecordRun(table, "fake/model"), "fake/model",
        new_id=lambda: next(ids),
    )  # fmt: skip


def propose(text: str = SAID, **reading: object) -> tuple[RecordReply, FakeAuditTable, FakeLedger]:
    table, found = FakeAuditTable(), ledger()
    reply = asyncio.run(proposer(FakeModel(lunch(**reading)), found, table)(text, NOW))
    return reply, table, found


def test_read_then_classify_then_propose_and_nothing_is_written():
    reply, table, found = propose()
    card = reply.card
    assert card is not None and card.proposal_id == "run-1"
    assert (card.occurred_on.isoformat(), card.category_name, card.amount, card.account_name) == (
        "2026-10-14",
        "식비",
        8500,
        "카드",
    )
    assert card.unsure == ()
    # 제안은 감사 테이블에 대기로 — api의 거래에는 아무것도 가지 않았다
    assert table.status_of("run-1") == ("awaiting_confirmation", "proposed")
    calls = table.rows["run-1"].run.tool_calls
    assert [c.tool for c in calls] == ["suggest_category", "create_transaction"]
    assert calls[1].args["amount"] == 8500 and calls[1].args["account"] == "card"
    assert all(method != "create_transaction" for method, _ in found.calls)


def test_what_was_not_read_is_defaulted_and_said():
    reply, _, _ = propose("이것저것 7700원", merchant="", payment="unknown")
    assert reply.card is not None
    assert (reply.card.category_name, reply.card.account_name) == ("기타", "카드")
    assert reply.card.unsure == ("category", "account")


def test_no_card_when_the_proposal_cannot_be_kept():
    table, found = FakeAuditTable(), ledger()
    table.fail = LedgerUnavailable("ConnectError")
    reply = asyncio.run(proposer(FakeModel(lunch()), found, table)(SAID, NOW))
    assert reply.card is None and reply.code == "proposal_not_saved"


def test_a_refusal_is_said_and_left_in_the_audit_without_a_card():
    reply, table, _ = propose("얼마 썼어?", kind="question")
    assert reply.card is None and reply.text and not reply.code
    assert table.status_of("run-1") == ("done", "question")
