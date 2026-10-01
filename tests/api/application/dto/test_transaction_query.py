from __future__ import annotations

from api.application.dto import TransactionQuery


def test_no_filter_by_default():
    query = TransactionQuery()
    assert (query.start, query.end, query.direction, query.text) == (None, None, None, "")
