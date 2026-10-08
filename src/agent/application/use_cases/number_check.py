"""답의 숫자가 도구에서 왔는가(docs/ai/chat-analytics.md 7.2).

모델이 결과를 읽고 쓴 한 줄에서 숫자 토큰을 뽑아, 도구 결과에 있던 수치의 집합에 있는지
본다. 집합 밖 숫자가 하나라도 있으면 그 문장을 버린다 — "7건, 평균 5,200원"을 보고 쓴
"총 36,400원"은 맞든 틀리든 DB가 낸 값이 아니다. 날짜와 기간 경계의 숫자는 예외다.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from agent.application.dto import ToolStep

# 천 단위 쉼표와 소수점을 품은 숫자. "5,267원", "1.4일", "88%"의 숫자 부분
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_from_tools(steps: Iterable[ToolStep], today: date) -> set[str]:
    """답에 써도 되는 숫자 — 성공한 봉투의 수치(부호를 뗀 것도), 해석한 기간의 날짜, 오늘."""
    allowed: set[str] = set()
    for step in steps:
        result = step.result
        if result.data is None:
            continue
        _collect(result.data, allowed)
        _collect(step.call.arguments, allowed)  # "최근 3일"의 3, "8월"의 8
        if result.meta is not None:
            for span in result.meta.periods.values():
                last = span.end - timedelta(days=1)
                for moment in (span.start, last):
                    allowed |= _date_parts(moment)
    allowed |= _date_parts(today)
    return allowed


def unsupported(sentence: str, allowed: set[str]) -> list[str]:
    """문장에 있는데 도구 결과에 없는 숫자들. 비었으면 문장을 내보내도 된다."""
    return [n for n in (_normal(m) for m in _NUMBER.findall(sentence)) if n and n not in allowed]


def _collect(value: object, into: set[str]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, int | float):
        for number in (value, abs(value)):
            normal = _normal(str(number))
            if normal:
                into.add(normal)
    elif isinstance(value, str):
        for token in _NUMBER.findall(value):  # "2026-08" 같은 인자, ISO 시각
            normal = _normal(token)
            if normal:
                into.add(normal)
    elif isinstance(value, Mapping):
        for item in value.values():
            _collect(item, into)
    elif isinstance(value, list | tuple):
        for item in value:
            _collect(item, into)


def _date_parts(moment: date | datetime) -> set[str]:
    return {str(moment.year), str(moment.month), str(moment.day), f"{moment.year % 100:02d}"}


def _normal(token: str) -> str:
    """ "5,267"→"5267", "1.0"→"1", "1.40"→"1.4". 표기가 달라도 같은 수는 같게."""
    try:
        number = Decimal(token.replace(",", ""))
    except InvalidOperation:
        return ""
    normal = number.normalize()
    return format(normal, "f") if normal == normal.to_integral() else str(normal)
