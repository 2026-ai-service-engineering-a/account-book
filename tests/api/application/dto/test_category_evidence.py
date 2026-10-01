from __future__ import annotations

from datetime import datetime

from api.application.dto import CategoryEvidence
from api.domain.values import CategoryId, Money, TransactionId
from tests.api.conftest import SEOUL


def test_similarity_only_from_the_vector_step():
    evidence = CategoryEvidence(
        TransactionId("t1"),
        "김밥천국",
        "",
        CategoryId("food"),
        Money(1),
        datetime(2026, 9, 1, tzinfo=SEOUL),
    )
    assert evidence.similarity is None
