"""확인 게이트의 테이프 — 확인·취소·만료·두 번 확인·재시작(docs/ai/chat-capture.md 5장)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from agent.application.dto import RecordReply
from agent.application.errors import LedgerRejected, LedgerUnavailable
from agent.application.use_cases import DecideRecord
from agent.domain.tools import BudgetLine
from agent.domain.values import Amount, CategoryId
from tests.agent.application.use_cases.test_propose_record import NOW, SAID, ledger, lunch, proposer
from tests.agent.conftest import FakeLedger, FakeModel
from tests.agent.fake_audit import FakeAuditTable

CREATED_AT = datetime(2026, 10, 15, 3, tzinfo=UTC)
BUDGET = (
    BudgetLine(CategoryId("food"), "식비", Amount(182_300), Amount(300_000), Amount(117_700),
               61, None, None),
)  # fmt: skip


@dataclass
class Gate:
    """제안 하나가 카드로 나간 뒤의 자리 — 결정, 감사 테이블, 원장, 지금."""

    decide: DecideRecord
    table: FakeAuditTable
    found: FakeLedger
    run_id: str
    now: datetime = CREATED_AT + timedelta(minutes=1)

    def confirm(self, run_id: str | None = None) -> RecordReply:
        return asyncio.run(self.decide.confirm(run_id or self.run_id))

    def cancel(self) -> RecordReply:
        return asyncio.run(self.decide.cancel(self.run_id))

    def status(self, run_id: str | None = None) -> tuple[str, str]:
        return self.table.status_of(run_id or self.run_id)

    def writes(self) -> list[tuple[object, ...]]:
        return [args for method, args in self.found.calls if method == "create_transaction"]

    def keys(self) -> list[object]:
        return [args[1] for args in self.writes()]


def gate(found: FakeLedger | None = None) -> Gate:
    found = found or ledger(budget_status=BUDGET)
    table = FakeAuditTable(clock=lambda: CREATED_AT)  # 제안은 CREATED_AT에 남는다
    propose = proposer(FakeModel(lunch()), found, table)
    card = asyncio.run(propose(SAID, NOW)).card
    assert card is not None
    made = Gate(
        DecideRecord(table, found, propose, lambda: made.now), table, found, card.proposal_id
    )
    return made


def test_confirm_writes_with_the_proposal_key_and_says_the_budget():
    g = gate()
    reply = g.confirm()
    ((_, key, run_id),) = g.writes()
    assert (key, run_id) == (f"{g.run_id}:2", g.run_id)  # {run_id}:{seq} — 쓰기는 두 번째 호출
    assert g.status() == ("done", "confirmed")
    assert g.table.rows[g.run_id].results["c2"] == {"transaction_id": "t1"}
    assert reply.wrote and reply.text == "기록했어요.\n10월 식비 182,300원 / 예산 300,000원 (61%)."


def test_cancel_closes_without_writing_and_stays_closed():
    g = gate()
    assert g.cancel().text == "취소했어요. 기록하지 않았습니다."
    assert g.status() == ("aborted", "cancelled")
    assert "취소했거나" in g.confirm().text and "취소했거나" in g.cancel().text
    assert g.writes() == []


def test_after_24_hours_the_old_card_is_closed_and_a_new_one_is_proposed():
    g = gate()
    g.now = CREATED_AT + timedelta(hours=24)
    reply = g.confirm()
    assert g.status() == ("aborted", "expired")
    assert reply.card is not None and reply.card.proposal_id != g.run_id  # 새 run — 새 키
    assert g.status(reply.card.proposal_id) == ("awaiting_confirmation", "proposed")
    assert reply.text == "시간이 지나 다시 확인할게요." and g.writes() == []


def test_just_under_24_hours_it_still_lives():
    g = gate()
    g.now = CREATED_AT + timedelta(hours=23, minutes=59)
    assert g.confirm().wrote and len(g.writes()) == 1


def test_confirming_twice_writes_once():
    g = gate()
    assert g.confirm().text.startswith("기록했어요.")
    assert g.confirm().text == "이미 기록했어요."
    assert len(g.writes()) == 1


def test_a_click_after_a_crash_mid_write_goes_on_with_the_same_key():
    # 첫 확인이 confirmed_at만 남기고 죽었다(쓰는 중). 다음 확인은 같은 키로 이어 간다 —
    # 이미 들어갔다면 api가 저장된 응답을 돌려준다(api-contract 3장)
    g = gate()
    asyncio.run(g.table.confirm(g.run_id, "c2"))
    assert g.confirm().wrote
    assert g.keys() == [f"{g.run_id}:2"] and g.status() == ("done", "confirmed")


def test_the_other_click_is_told_it_is_in_progress():
    busy = LedgerRejected(409, "request_in_progress", {})
    g = gate(ledger(budget_status=BUDGET, create_transaction=busy))
    assert g.confirm().text == "이미 기록하고 있어요."
    assert g.status()[0] == "awaiting_confirmation"


def test_a_confirmed_proposal_is_not_cancelled():
    g = gate()
    asyncio.run(g.table.confirm(g.run_id, "c2"))
    assert g.cancel().text == "이미 기록하고 있어요."
    assert g.status()[0] == "awaiting_confirmation"


def test_after_a_restart_the_proposal_is_read_back_from_the_table():
    g = gate()
    fresh = proposer(FakeModel(), g.found, g.table)
    restarted = DecideRecord(g.table, g.found, fresh, lambda: g.now)  # 메모리에 아무것도 없다
    assert asyncio.run(restarted.confirm(g.run_id)).wrote
    assert g.keys() == [f"{g.run_id}:2"]


def test_an_unreachable_api_keeps_it_waiting_and_the_next_click_uses_the_same_key():
    g = gate(ledger(budget_status=BUDGET, create_transaction=LedgerUnavailable("ConnectError")))
    reply = g.confirm()
    assert reply.code == "ledger_unavailable" and g.status()[0] == "awaiting_confirmation"
    assert g.table.rows[g.run_id].confirmed_at  # 확인은 남았다 — 다음 누름은 쓰는 중으로 이어 간다
    g.confirm()
    assert g.keys() == [f"{g.run_id}:2", f"{g.run_id}:2"]


def test_a_rejected_write_closes_as_failed():
    refused = LedgerRejected(422, "validation_error", {"category_id": "없는 카테고리입니다."})
    g = gate(ledger(create_transaction=refused))
    reply = g.confirm()
    assert reply.code == "validation_error" and "없는 카테고리" in reply.text
    assert g.status() == ("failed", "rejected")


def test_an_unknown_proposal():
    assert gate().confirm("nope").code == "not_found"
