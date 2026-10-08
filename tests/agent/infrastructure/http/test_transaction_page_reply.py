from __future__ import annotations

from agent.domain.values import Amount, Direction
from agent.infrastructure.http.transaction_page_reply import TransactionPageReply

ITEM = {
    "id": "t1",
    "direction": "expense",
    "amount": 5800,
    "occurred_at": "2026-10-02T08:10:00+00:00",
    "category_id": "cafe",
    "account_id": "card",
    "merchant": "스타벅스",
    "memo": "",
    "source": "manual",
    "run_id": None,
}


def test_reads_the_fields_the_tool_shows():
    page = TransactionPageReply.model_validate({"items": [ITEM], "next_cursor": "c"}).page()
    (line,) = page.transactions
    assert (line.amount, line.direction) == (Amount(5800), Direction.EXPENSE)
    assert line.merchant == "스타벅스"
    assert page.has_more


def test_last_page_has_no_more():
    last = TransactionPageReply.model_validate({"items": [], "next_cursor": None})
    assert not last.page().has_more
