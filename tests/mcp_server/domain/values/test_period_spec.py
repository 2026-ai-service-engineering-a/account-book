from __future__ import annotations

from datetime import date

import pytest

from mcp_server.domain.values import PeriodName, PeriodSpec
from tests.mcp_server.conftest import SEOUL


def test_last_week_starts_on_monday_and_leaves_today_out():
    found = PeriodSpec(PeriodName.LAST_WEEK).bounds(date(2026, 10, 15), SEOUL)
    assert (found.start.date(), found.end.date()) == (date(2026, 10, 5), date(2026, 10, 12))


@pytest.mark.parametrize(
    "spec",
    [
        {"name": PeriodName.THIS_MONTH, "days": 3},
        {"name": PeriodName.LAST_N_DAYS, "days": 366},
        {"name": PeriodName.MONTH, "start": date(2026, 2, 3)},
        {"name": PeriodName.RANGE, "start": date(2026, 9, 5), "end": date(2026, 9, 3)},
    ],
)
def test_values_that_do_not_belong_to_the_name_are_refused(spec):
    with pytest.raises(ValueError):
        PeriodSpec(**spec)
