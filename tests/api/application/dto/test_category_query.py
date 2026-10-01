from __future__ import annotations

from api.application.dto import CategoryQuery
from api.domain.values import Direction


def test_no_vector_step_without_a_model():
    query = CategoryQuery("카페", "", Direction.EXPENSE)
    assert query.embedding_model == "" and query.query_vector is None
