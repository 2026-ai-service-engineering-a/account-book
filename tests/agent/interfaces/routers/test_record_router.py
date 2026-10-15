from __future__ import annotations

import json

from agent.application.errors import LedgerUnavailable, ModelUnavailable
from tests.agent.application.use_cases.test_decide_record import BUDGET
from tests.agent.application.use_cases.test_propose_record import NOW, SAID, ledger, lunch
from tests.agent.conftest import FakeModel
from tests.agent.fake_audit import FakeAuditTable
from tests.agent.interfaces.conftest import client_with
from tests.agent.interfaces.routers.test_chat_router import events

BODY = {"text": SAID, "now": NOW.isoformat(), "timezone": "Asia/Seoul"}


def test_a_card_then_confirm_then_done():
    table = FakeAuditTable()
    client = client_with(
        FakeModel(lunch()), ledger(budget_status=BUDGET), recorder=table, book=table
    )
    proposed = events(client.post("/record", json=BODY).text)
    assert [k for k, _ in proposed] == ["tool", "tool", "proposal", "done"]
    card = json.loads(proposed[2][1])
    assert (card["amount"], card["category_name"], card["unsure"]) == (8500, "식비", [])
    confirmed = events(client.post(f"/record/proposals/{card['id']}/confirm").text)
    assert [k for k, _ in confirmed] == ["tool", "message", "done"]
    assert confirmed[1][1].startswith("기록했어요.")


def test_cancel_and_an_unknown_proposal():
    table = FakeAuditTable()
    client = client_with(FakeModel(lunch()), ledger(), recorder=table, book=table)
    card = json.loads(events(client.post("/record", json=BODY).text)[2][1])
    cancelled = events(client.post(f"/record/proposals/{card['id']}/cancel").text)
    assert cancelled[0] == ("message", "취소했어요. 기록하지 않았습니다.")
    missing = events(client.post("/record/proposals/nope/confirm").text)
    assert missing[0][0] == "error" and json.loads(missing[0][1])["code"] == "not_found"


def test_no_card_when_the_model_is_down():
    client = client_with(FakeModel(ModelUnavailable("x")), ledger())
    down = events(client.post("/record", json=BODY).text)
    assert [k for k, _ in down] == ["error", "done"]
    assert json.loads(down[0][1])["code"] == "model_unavailable"


def test_no_card_when_the_proposal_is_not_kept():
    unkept = FakeAuditTable()
    unkept.fail = LedgerUnavailable("ConnectError")
    client = client_with(FakeModel(lunch()), ledger(), recorder=unkept, book=unkept)
    found = events(client.post("/record", json=BODY).text)
    assert [k for k, _ in found] == ["error", "done"]
    assert json.loads(found[0][1])["code"] == "proposal_not_saved"
