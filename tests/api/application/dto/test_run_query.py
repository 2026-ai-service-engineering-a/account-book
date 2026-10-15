from __future__ import annotations

from api.application.dto import RunQuery


def test_everything_newest_first_by_default():
    query = RunQuery()
    assert (query.seat, query.status, query.cursor, query.limit) == (None, None, None, 30)
