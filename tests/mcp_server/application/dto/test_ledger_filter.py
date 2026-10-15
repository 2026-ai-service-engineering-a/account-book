from __future__ import annotations

from datetime import datetime

from mcp_server.application.dto import LedgerFilter
from mcp_server.domain.values import TimeRange
from tests.mcp_server.conftest import SEOUL


def test_narrows_nothing_by_default():
    period = TimeRange(datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 11, 1, tzinfo=SEOUL))
    where = LedgerFilter(period)
    assert (where.category_id, where.text, where.direction) == ("", "", None)
