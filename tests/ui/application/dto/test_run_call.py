from __future__ import annotations

from ui.application.dto import RunCall


def test_a_waiting_proposal_has_no_result_yet():
    call = RunCall("c2", "create_transaction", {"amount": 8500}, None, None)
    assert call.result is None and call.confirmed_at is None
