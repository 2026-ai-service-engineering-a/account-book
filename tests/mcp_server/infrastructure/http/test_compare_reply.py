from __future__ import annotations

from mcp_server.infrastructure.http.compare_reply import CompareReply


def test_flattens_the_category():
    reply = [
        {"category": {"id": "food", "name": "식비"}, "a": 100, "b": 150, "delta": 50, "percent": 50}
    ]
    (row,) = CompareReply.model_validate(reply).rows()
    assert (row["category_id"], row["name"], row["delta"], row["percent"]) == (
        "food",
        "식비",
        {"amount": 50, "currency": "KRW"},
        50,
    )
