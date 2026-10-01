from __future__ import annotations

from api.application.dto import TransactionQuery
from api.domain.values import CategoryId, Direction
from api.infrastructure.db.transaction_filter import filter_conditions


def test_one_condition_per_given_filter():
    assert filter_conditions(TransactionQuery()) == []
    query = TransactionQuery(direction=Direction.EXPENSE, category_id=CategoryId("food"), text="김")
    assert len(filter_conditions(query)) == 3
