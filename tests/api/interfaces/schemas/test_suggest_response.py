from __future__ import annotations

from datetime import datetime

from api.application.dto import CategoryCandidate, CategoryEvidence, CategorySearch, SearchStrategy
from api.domain.entities import Category
from api.domain.values import CategoryId, Direction, Money, TransactionId
from api.interfaces.schemas import SuggestResponse
from tests.api.conftest import SEOUL


def test_the_shape_the_agent_reads():
    search = CategorySearch(
        SearchStrategy.VECTOR,
        "블루보틀",
        False,
        (CategoryCandidate(CategoryId("cafe"), 0.9),),
        (
            CategoryEvidence(
                TransactionId("t1"),
                "스타벅스",
                "",
                CategoryId("cafe"),
                Money(5800),
                datetime(2026, 9, 12, 13, tzinfo=SEOUL),
                0.71,
            ),
        ),
        (Category(CategoryId("cafe"), "카페", Direction.EXPENSE),),
    )
    body = SuggestResponse.of(search).model_dump(mode="json")
    assert body["strategy"] == "vector" and body["evidence"][0]["amount"] == 5800
    assert body["categories"][0] == {"id": "cafe", "name": "카페", "direction": "expense"}
