"""조회 기간을 UTC 경계로. 목록과 합계가 같은 식으로 풀어야 둘이 다른 거래를 세지 않는다."""

from __future__ import annotations

from datetime import datetime, tzinfo

from api.domain.values import Period, TimeRange


def bounds(
    period: Period | TimeRange | None, zone: tzinfo
) -> tuple[datetime | None, datetime | None]:
    """달은 사용자 타임존으로 풀고(development-rules 6.1), 경계는 받은 그대로 쓴다."""
    if isinstance(period, TimeRange):
        return period.start, period.end
    return period.bounds(zone) if period else (None, None)
