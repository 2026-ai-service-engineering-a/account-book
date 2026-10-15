from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from api.domain.rules.usual_range import baseline_start, unjudged, usual_upper
from api.domain.values import Money, SkipReason

SEOUL = ZoneInfo("Asia/Seoul")


@pytest.mark.parametrize(
    ("start", "since"),
    [
        (datetime(2026, 10, 1, tzinfo=SEOUL), datetime(2026, 4, 1, tzinfo=SEOUL)),
        (datetime(2026, 3, 1, tzinfo=SEOUL), datetime(2025, 9, 1, tzinfo=SEOUL)),  # 해를 넘는다
        (datetime(2026, 8, 31, tzinfo=SEOUL), datetime(2026, 2, 28, tzinfo=SEOUL)),  # 말일로
    ],
)
def test_six_months_before_in_the_users_months(start, since):
    assert baseline_start(start, SEOUL) == since


def test_a_utc_boundary_is_counted_in_the_users_zone():
    # 서울의 10월 1일 0시는 UTC로 9월 30일 15시다. 여섯 달 전은 서울의 4월 1일이다
    start = datetime(2026, 9, 30, 15, tzinfo=ZoneInfo("UTC"))
    assert baseline_start(start, SEOUL) == datetime(2026, 4, 1, tzinfo=SEOUL)


def test_the_upper_is_the_median_plus_the_scaled_spread():
    # 3.5 * 1.4826 * 2,000 = 10,378.2 → 10,379원 위
    assert usual_upper(Money(9000), Money(2000)) == Money(19379)


def test_no_spread_still_needs_twice_the_median():
    # 매달 9,900원 구독: 산포가 0이라도 10,900원은 평소다
    assert usual_upper(Money(9900), Money(0)) == Money(19800)


def test_why_a_category_is_not_judged():
    since = datetime(2026, 4, 1, tzinfo=SEOUL)
    assert unjudged(datetime(2026, 5, 3, tzinfo=SEOUL), since, 30) is SkipReason.SHORT_HISTORY
    assert unjudged(datetime(2025, 1, 1, tzinfo=SEOUL), since, 4) is SkipReason.TOO_FEW
    assert unjudged(since, since, 5) is None  # 딱 여섯 달이면 판정한다


def test_a_category_that_starts_in_the_period_is_short_history():
    assert unjudged(None, datetime(2026, 4, 1, tzinfo=SEOUL), 0) is SkipReason.SHORT_HISTORY
