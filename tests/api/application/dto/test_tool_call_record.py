from __future__ import annotations

from api.application.dto import ToolCallRecord


def test_a_refused_call_has_no_result():
    call = ToolCallRecord("c1", "create_transaction", {"amount": 8500}, None)
    assert call.result is None and call.args["amount"] == 8500
