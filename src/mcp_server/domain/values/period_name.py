from __future__ import annotations

from enum import StrEnum


class PeriodName(StrEnum):
    """도구가 받는 기간의 이름. 바깥 모델은 이름만 고르고, 경계는 `PeriodSpec.bounds`가 낸다.

    외부 모델이 날짜를 계산하면 주의 시작이 일요일이 되거나 타임존이 UTC가 된다
    (docs/ai/chat-analytics.md 5장). 목록은 계약의 enum과 같다.
    """

    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_YEAR = "this_year"
    LAST_N_DAYS = "last_n_days"  # days를 같이 받는다
    MONTH = "month"  # start(그 달 1일)를 같이 받는다
    RANGE = "range"  # start·end(끝 날짜 포함)를 같이 받는다
