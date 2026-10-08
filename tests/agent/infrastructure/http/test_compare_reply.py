from __future__ import annotations

from agent.domain.values import Amount
from agent.infrastructure.http.compare_reply import CompareReply

ROW = {
    "category": {"id": "cafe", "name": "카페", "direction": "expense"},
    "a": 17600,
    "b": 6300,
    "delta": -11300,
    "percent": 64,
}


def test_one_shift_per_category():
    (shift,) = CompareReply.model_validate([ROW]).shifts()
    assert (shift.category_id, shift.name, shift.delta, shift.percent) == (
        "cafe",
        "카페",
        Amount(-11300),
        64,
    )
