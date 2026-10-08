from __future__ import annotations

from enum import StrEnum


class PeriodName(StrEnum):
    """질문이 말한 기간의 이름. LLM은 이름만 고르고, 경계는 `PeriodSpec.bounds`가 계산한다.

    "저번 주"가 며칠부터인지 모델이 계산하면 주의 시작이 일요일이 되거나 오늘이 끼거나
    타임존이 UTC가 된다. 셋 다 사용자가 알아채지 못한다(ai/chat-analytics.md 5장).
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
    RANGE = "range"  # start·end(끝 날짜 포함)를 같이 받는다. 날짜를 직접 말한 질문만
