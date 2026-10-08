from __future__ import annotations

from datetime import datetime

from agent.application.dto import TransactionFilter
from agent.domain.values import TimeRange
from tests.agent.conftest import SEOUL


def test_only_the_period_is_needed():
    week = TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL))
    found = TransactionFilter(week)
    assert (found.category_id, found.text, found.direction) == (None, "", None)
