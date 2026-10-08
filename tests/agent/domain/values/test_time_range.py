from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from agent.domain.values import TimeRange
from tests.agent.conftest import SEOUL

SEPTEMBER = TimeRange(datetime(2026, 9, 1, tzinfo=SEOUL), datetime(2026, 10, 1, tzinfo=SEOUL))


def test_rejects_naive_and_backwards_bounds():
    with pytest.raises(ValueError, match="aware"):
        TimeRange(datetime(2026, 9, 1), SEPTEMBER.end)
    with pytest.raises(ValueError, match="끝"):
        TimeRange(SEPTEMBER.end, SEPTEMBER.start)


def test_first_part_never_runs_past_the_end():
    assert SEPTEMBER.first(timedelta(days=8)).end == datetime(2026, 9, 9, tzinfo=SEOUL)
    assert SEPTEMBER.first(timedelta(days=99)) == SEPTEMBER
