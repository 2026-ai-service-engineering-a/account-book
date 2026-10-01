from __future__ import annotations

from datetime import datetime

from tests.ui.conftest import SEOUL
from ui.application.dto import CategoryEvidence
from ui.application.values import CategoryId, Money, TransactionId


def test_similarity_only_from_the_vector_step():
    evidence = CategoryEvidence(
        TransactionId("t1"),
        "김밥천국",
        "",
        CategoryId("food"),
        Money(8500),
        datetime(2026, 9, 1, tzinfo=SEOUL),
    )
    assert evidence.similarity is None
