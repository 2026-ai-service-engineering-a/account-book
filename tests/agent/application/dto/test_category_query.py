from __future__ import annotations

from agent.application.dto import CategoryQuery
from agent.domain.values import Direction


def test_no_vector_until_asked():
    query = CategoryQuery("카페", "", Direction.EXPENSE)
    assert query.embedding_model == "" and query.query_vector is None
