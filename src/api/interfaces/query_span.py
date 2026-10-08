"""쿼리 문자열의 기간을 값으로. `period=YYYY-MM`과 `from`/`to` 중 하나만 받는다(api-contract 6장).

달은 화면이 쓰고, 경계는 agent가 쓴다 — "저번 주"를 날짜로 푸는 쪽이 경계를 넘긴다
(ai/chat-analytics.md 5장). 틀린 기간은 다른 422와 같은 길(RequestValidationError)로 낸다.
"""

from __future__ import annotations

from datetime import datetime

from fastapi.exceptions import RequestValidationError

from api.domain.values import Period, TimeRange


def time_range(start: datetime, end: datetime, field: str) -> TimeRange:
    """`[start, end)`. 뒤집힌 기간은 끝 필드(`field`)를 짚어 422로."""
    try:
        return TimeRange(start, end)
    except ValueError as error:
        raise _invalid(field, str(error)) from error


def period_or_range(
    period: str | None, start: datetime | None, end: datetime | None
) -> Period | TimeRange | None:
    """`period`(이미 모양을 검사한 YYYY-MM)나 `from`·`to` 한 쌍. 아무것도 없으면 None."""
    if start is None and end is None:
        return Period.parse(period) if period else None
    if period is not None:
        raise _invalid("period", "period와 from·to는 함께 쓰지 않는다")
    if start is None:
        raise _invalid("from", "from과 to는 함께 온다")
    if end is None:
        raise _invalid("to", "from과 to는 함께 온다")
    return time_range(start, end, "to")


def _invalid(field: str, message: str) -> RequestValidationError:
    error = {"loc": ("query", field), "msg": message, "type": "value_error"}
    return RequestValidationError([error])
