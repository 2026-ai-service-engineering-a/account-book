from __future__ import annotations

from enum import StrEnum


class SaidDay(StrEnum):
    """한 줄에서 날짜를 어떻게 말했나. 날짜 자체가 아니라 말한 방식이다.

    LLM은 이 이름만 고른다. 실제 날짜는 `SaidWhen.resolve`가 기준 시각으로 계산한다
    (docs/ai/README.md 2장 원칙 2).
    """

    UNSPECIFIED = "unspecified"
    TODAY = "today"
    YESTERDAY = "yesterday"
    DAY_BEFORE_YESTERDAY = "day_before_yesterday"
    DATE = "date"  # "09/16"처럼 월·일을 적었다. 연도는 없다
