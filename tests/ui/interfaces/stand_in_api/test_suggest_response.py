from __future__ import annotations

from datetime import datetime

from tests.ui.conftest import SEOUL
from ui.application.dto import (
    Category,
    CategoryCandidate,
    CategoryEvidence,
    CategorySearch,
    Direction,
    SearchStrategy,
)
from ui.application.values import CategoryId, Money, TransactionId
from ui.interfaces.stand_in_api import SuggestResponse


def test_plain_values_on_the_wire():
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
    assert body["categories"] == [{"id": "cafe", "name": "카페"}]
