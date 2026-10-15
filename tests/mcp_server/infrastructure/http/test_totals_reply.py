from __future__ import annotations

from mcp_server.infrastructure.http.totals_reply import TotalsReply


def test_turns_into_the_tool_shape():
    row = TotalsReply.model_validate({"expense": 412000, "income": 0}).row()
    assert row == {
        "expense": {"amount": 412000, "currency": "KRW"},
        "income": {"amount": 0, "currency": "KRW"},
    }
