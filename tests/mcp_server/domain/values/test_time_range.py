from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from mcp_server.domain.values import TimeRange
from tests.mcp_server.conftest import SEOUL


def test_first_keeps_the_start_and_never_grows():
    whole = TimeRange(datetime(2026, 9, 1, tzinfo=SEOUL), datetime(2026, 10, 1, tzinfo=SEOUL))
    assert whole.first(timedelta(days=15)).end == datetime(2026, 9, 16, tzinfo=SEOUL)
    assert whole.first(timedelta(days=90)) == whole


def test_naive_or_empty_ranges_are_refused():
    with pytest.raises(ValueError):
        TimeRange(datetime(2026, 9, 1), datetime(2026, 10, 1))
    with pytest.raises(ValueError):
        TimeRange(datetime(2026, 9, 1, tzinfo=SEOUL), datetime(2026, 9, 1, tzinfo=SEOUL))
