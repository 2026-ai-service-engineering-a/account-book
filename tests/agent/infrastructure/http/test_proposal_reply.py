from __future__ import annotations

import pytest

from agent.application.errors import LedgerUnavailable
from agent.infrastructure.http.proposal_reply import ProposalReply

RUN = {
    "id": "r1",
    "seat": "capture",
    "flow": "single",
    "utterance": "김밥천국 8500원",
    "status": "awaiting_confirmation",
    "stop_reason": "proposed",
    "created_at": "2026-10-15T03:00:00+00:00",
    "tool_calls": [
        {"call_id": "c1", "tool": "suggest_category", "args": {}, "result": {},
         "confirmed_at": None},
        {"call_id": "c2", "tool": "create_transaction", "args": {"amount": 8500}, "result": None,
         "confirmed_at": None},
    ],
}  # fmt: skip


def test_reads_the_write_call_as_the_proposal():
    found = ProposalReply.model_validate(RUN).proposal()
    assert (found.call_id, found.args, found.idempotency_key) == ("c2", {"amount": 8500}, "r1:2")


def test_a_run_without_a_write_is_not_a_proposal():
    with pytest.raises(LedgerUnavailable):
        ProposalReply.model_validate(RUN | {"tool_calls": RUN["tool_calls"][:1]}).proposal()
