from __future__ import annotations

from ui.application.dto import CategoryQuery, Direction


def test_without_model_there_is_no_vector_step():
    query = CategoryQuery("카페", "", Direction.EXPENSE)
    assert query.embedding_model == "" and query.query_vector is None
