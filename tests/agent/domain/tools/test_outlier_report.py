from __future__ import annotations

from datetime import UTC, datetime

from agent.domain.tools import OutlierReport
from agent.domain.values import TimeRange
from tests.agent.domain.tools.test_outlier_line import big_one

BASELINE = TimeRange(datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 9, 1, tzinfo=UTC))


def report() -> OutlierReport:
    return OutlierReport(BASELINE, (big_one(),), False, ())


def test_nothing_skipped_means_every_category_was_judged():
    assert report().skipped == () and len(report().items) == 1
