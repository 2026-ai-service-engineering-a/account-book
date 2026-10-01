from __future__ import annotations

from datetime import UTC, datetime

import pytest

from api.infrastructure.db.page_cursor import decode_cursor, encode_cursor


def test_round_trip_and_opaque():
    at = datetime(2026, 9, 16, 3, 30, tzinfo=UTC)
    cursor = encode_cursor(at, "t1")
    assert "2026" not in cursor and decode_cursor(cursor) == (at, "t1")


@pytest.mark.parametrize("bad", ["", "!!!", "bm9waXBl", encode_cursor(datetime(2026, 9, 1), "t")])
def test_unreadable_cursor_restarts_from_the_first_page(bad):
    assert decode_cursor(bad) is None
