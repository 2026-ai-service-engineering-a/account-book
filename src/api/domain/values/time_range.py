from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TimeRange:
    """집계 기간 `[start, end)`. 끝은 열린 구간이다(development-rules 6.1).

    경계는 이미 풀려서 온다. "저번 주"가 며칠부터인지는 부르는 쪽이 사용자 타임존으로
    정한다 — 기간 이름은 여기까지 오지 않는다(ai/chat-analytics.md 5장).
    """

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("기간 경계는 시간대가 붙은 시각이어야 한다")
        if self.start >= self.end:
            raise ValueError("기간의 끝은 시작보다 뒤여야 한다")
