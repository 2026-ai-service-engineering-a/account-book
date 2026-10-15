from __future__ import annotations

from mcp_server.infrastructure.http.budget_status_reply import BudgetStatusReply

CATEGORY = {"id": "food", "name": "식비"}


def test_a_budget_line_and_a_line_without_a_budget():
    reply = [
        {"category": CATEGORY, "limit": 400000, "spent": 300000, "remaining": 100000,
         "percent": 75, "projected": 620000, "over_on": "2026-10-20"},
        {"category": CATEGORY, "limit": None, "spent": 5000, "remaining": None,
         "percent": None, "projected": None, "over_on": None},
    ]  # fmt: skip
    planned, unplanned = BudgetStatusReply.model_validate(reply).rows()
    assert planned["over_on"] == "2026-10-20" and planned["limit"] == {
        "amount": 400000,
        "currency": "KRW",
    }
    assert unplanned["limit"] is None and unplanned["spent"] == {"amount": 5000, "currency": "KRW"}
