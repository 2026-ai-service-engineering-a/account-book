"""평소 범위 — 카테고리별 최근 여섯 달의 중앙값과 산포로 평소를 벗어난 거래를 가른다.

기준은 여기 한 곳에서 정한다. 부르는 쪽은 임계값을 넘기지 않는다 — 모델이 임계값을 말하기
시작하면 같은 데이터가 달마다 다르게 특이해진다(docs/ai/agentic-reports.md 3장).

- 산포는 표준편차가 아니라 MAD(중앙값에서 떨어진 거리의 중앙값)다. 특이한 한 건이 평균과
  표준편차를 같이 끌어올려 자기를 평범하게 만드는 일이 없다.
- 위쪽만 본다. 평소보다 적게 쓴 한 건은 리포트가 짚을 일이 아니다.
- 지난 여섯 달의 최댓값도 바닥이다. 점심과 주말 저녁이 섞인 식비, 지하철과 가끔의 택시가
  섞인 교통은 중앙값이 작은 쪽에 붙어서, 바닥이 없으면 늘 있던 저녁·택시가 매달 특이해진다.
  12달 데모에서 이 바닥 없이 달마다 2~9건, 있으면 0~2건이었다. "여섯 달 중 가장 큰 금액"은
  문장이 그대로 근거로 들 수 있는 말이기도 하다.
"""

from __future__ import annotations

import calendar
import math
from datetime import datetime, tzinfo

from api.domain.values import Money, SkipReason

BASELINE_MONTHS = 6
MIN_BASELINE = 5  # 기준 기간의 거래가 이보다 적으면 중앙값·MAD가 뜻을 잃는다
_MAD_TO_SIGMA = 1.4826  # 정규분포에서 MAD를 표준편차 눈금으로 옮기는 상수
_Z_LIMIT = 3.5  # 수정 z 점수의 관례적 경계(Iglewicz·Hoaglin)
# 산포가 0이어도(매달 같은 금액의 구독) 중앙값의 두 배는 넘어야 특이하다. 900원 오른 구독료는 아니다
_FLOOR_RATIO = 2


def baseline_start(start: datetime, zone: tzinfo) -> datetime:
    """`start` 직전 여섯 달의 시작. 달은 사용자 타임존으로 센다(development-rules 6.1).

    31일에서 여섯 달을 빼면 그 달의 말일이 된다 — 없는 날을 만들지 않는다.
    """
    local = start.astimezone(zone)
    months = local.year * 12 + (local.month - 1) - BASELINE_MONTHS
    year, month = divmod(months, 12)
    day = min(local.day, calendar.monthrange(year, month + 1)[1])
    return local.replace(year=year, month=month + 1, day=day)


def usual_upper(median: Money, mad: Money, largest: Money) -> Money:
    """이 금액을 넘는 거래가 평소 범위를 벗어난 것이다(같으면 평소다). `largest`는 평소 기간의
    가장 큰 거래다."""
    spread = math.ceil(_Z_LIMIT * _MAD_TO_SIGMA * mad.amount)
    return Money(max(median.amount + spread, median.amount * _FLOOR_RATIO, largest.amount))


def unjudged(first_at: datetime | None, since: datetime, count: int) -> SkipReason | None:
    """판정하지 않는 이유. 판정할 수 있으면 None. `first_at`이 없으면 판정 기간이 첫 거래다."""
    if first_at is None or first_at > since:
        return SkipReason.SHORT_HISTORY
    if count < MIN_BASELINE:
        return SkipReason.TOO_FEW
    return None
