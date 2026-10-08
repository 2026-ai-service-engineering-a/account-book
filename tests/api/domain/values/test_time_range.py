from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from api.domain.values import TimeRange

SEOUL = ZoneInfo("Asia/Seoul")


def test_half_open_range_of_aware_times():
    start, end = datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 10, 5, tzinfo=SEOUL)
    assert TimeRange(start, end).end == end


def test_rejects_naive_bounds():
    with pytest.raises(ValueError, match="시간대"):
        TimeRange(datetime(2026, 9, 28), datetime(2026, 10, 5, tzinfo=SEOUL))


@pytest.mark.parametrize("end_day", [28, 27])
def test_end_must_come_after_start(end_day):
    with pytest.raises(ValueError, match="끝"):
        TimeRange(datetime(2026, 9, 28, tzinfo=SEOUL), datetime(2026, 9, end_day, tzinfo=SEOUL))
