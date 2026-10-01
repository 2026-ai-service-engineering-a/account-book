from __future__ import annotations

from datetime import datetime

from api.application.dto import CategoryEvidence
from api.domain.values import CategoryId, Money, TransactionId
from api.interfaces.schemas import EvidenceBody
from tests.api.conftest import SEOUL


def test_whole_won_and_similarity():
    evidence = CategoryEvidence(
        TransactionId("t1"),
        "m",
        "",
        CategoryId("food"),
        Money(8500),
        datetime(2026, 9, 1, tzinfo=SEOUL),
        0.9,
    )
    body = EvidenceBody.of(evidence)
    assert body.amount == 8500 and body.similarity == 0.9
