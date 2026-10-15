from __future__ import annotations

from agent.infrastructure.http.created_reply import CreatedReply


def test_reads_the_created_line():
    reply = CreatedReply.model_validate(
        {
            "id": "t1",
            "direction": "expense",
            "amount": 8500,
            "occurred_at": "2026-10-14T03:30:00+00:00",
            "category_id": "food",
            "merchant": "김밥천국",
            "memo": "",
            "account_id": "card",
        }
    )
    assert reply.line().amount.amount == 8500
