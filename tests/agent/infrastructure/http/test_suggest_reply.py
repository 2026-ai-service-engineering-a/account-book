from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.application.dto import SearchStrategy
from agent.infrastructure.http import SuggestReply

BODY = {
    "strategy": "vector",
    "query_text": "블루보틀",
    "needs_query_vector": False,
    "candidates": [{"category_id": "cafe", "confidence": 0.9}],
    "evidence": [
        {
            "transaction_id": "t1",
            "merchant": "스타벅스",
            "memo": "",
            "category_id": "cafe",
            "amount": 5800,
            "occurred_at": "2026-09-12T13:10:00+09:00",
            "similarity": 0.71,
        }
    ],
    "categories": [{"id": "cafe", "name": "카페"}],
}


def test_becomes_a_search_result():
    result = SuggestReply.model_validate(BODY).result()
    assert result.strategy is SearchStrategy.VECTOR
    assert result.candidates[0].confidence.value == 0.9
    assert result.evidence[0].amount.amount == 5800 and str(result.evidence[0].day) == "2026-09-12"


@pytest.mark.parametrize("broken", [{"strategy": "guess"}, {"candidates": [{"category_id": 1}]}])
def test_rejects_unknown_shapes(broken):
    with pytest.raises(ValidationError):
        SuggestReply.model_validate(BODY | broken)
