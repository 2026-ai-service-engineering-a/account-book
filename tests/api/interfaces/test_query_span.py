from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.exceptions import RequestValidationError

from api.domain.values import Period, TimeRange
from api.interfaces.query_span import period_or_range, time_range

SEOUL = ZoneInfo("Asia/Seoul")
START = datetime(2026, 9, 28, tzinfo=SEOUL)
END = datetime(2026, 10, 5, tzinfo=SEOUL)


def _field(error: pytest.ExceptionInfo[RequestValidationError]) -> object:
    return error.value.errors()[0]["loc"][-1]


def test_month_or_range_or_nothing():
    assert period_or_range("2026-09", None, None) == Period(2026, 9)
    assert period_or_range(None, START, END) == TimeRange(START, END)
    assert period_or_range(None, None, None) is None


def test_month_and_range_together_point_at_period():
    with pytest.raises(RequestValidationError) as error:
        period_or_range("2026-09", START, END)
    assert _field(error) == "period"


@pytest.mark.parametrize(("start", "end", "field"), [(START, None, "to"), (None, END, "from")])
def test_half_a_range_points_at_the_missing_end(start, end, field):
    with pytest.raises(RequestValidationError) as error:
        period_or_range(None, start, end)
    assert _field(error) == field


def test_backwards_range_points_at_the_given_field():
    with pytest.raises(RequestValidationError) as error:
        time_range(END, START, "a_to")
    assert _field(error) == "a_to"
