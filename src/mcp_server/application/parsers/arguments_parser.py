"""바깥 모델이 낸 인자(JSON)를 `ToolRequest`로. `Any`(모양을 모르는 값)는 여기서 끝난다.

인자 검증이 유일한 방어선이다 — 바깥 모델은 우리가 프롬프트를 고칠 수 없는 모델이다
(docs/ai/mcp.md 7.1). 기간을 받는 규칙은 agent와 같고, 공유 사례표가 그것을 맞춘다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date

from mcp_server.application.errors import InvalidArguments
from mcp_server.domain.tools import ToolName, ToolRequest
from mcp_server.domain.values import MAX_DAYS, Direction, PeriodName, PeriodSpec

_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_PERIOD_KEYS = {"name", "days", "month", "start", "end"}
_TEXT_LIMIT = 100  # api의 q 상한
_KEYS: Mapping[ToolName, set[str]] = {
    ToolName.SUMMARIZE_SPENDING: {"period", "category_id", "merchant", "direction"},
    ToolName.COUNT_FREQUENCY: {"period", "category_id", "merchant", "direction"},
    ToolName.COMPARE_PERIODS: {"a", "b", "category_id"},
    ToolName.GET_BUDGET_STATUS: {"period", "category_id"},
}


def parse_arguments(name: ToolName, raw: Mapping[str, object]) -> ToolRequest:
    keys = _KEYS[name]
    unknown = sorted(set(raw) - keys)
    if unknown:
        accepted = ", ".join(sorted(keys))
        raise InvalidArguments(unknown[0], f"이 도구가 받지 않는 인자다. 받는 것: {accepted}")
    periods = ("a", "b") if name is ToolName.COMPARE_PERIODS else ("period",)
    direction = None if "direction" not in keys else _direction(raw)
    if name is ToolName.COUNT_FREQUENCY:
        direction = direction or Direction.EXPENSE  # 몇 번 갔나는 지출을 센다
    return ToolRequest(
        name=name,
        periods={key: _period(raw, key) for key in periods},
        category_id=_text(raw, "category_id"),
        merchant=_text(raw, "merchant"),
        direction=direction,
    )


def _period(raw: Mapping[str, object], key: str) -> PeriodSpec:
    value = raw.get(key)
    if isinstance(value, str):  # 이름만 넘긴 것 — `period: "last_week"`도 받는다
        value = {"name": value}
    if not isinstance(value, Mapping):
        raise InvalidArguments(key, "기간은 {'name': 기간 이름} 모양이어야 한다")
    unknown = sorted(set(value) - _PERIOD_KEYS)
    if unknown:
        raise InvalidArguments(key, f"기간이 받지 않는 값이다: {unknown[0]}")
    try:
        name = PeriodName(str(value.get("name")))
    except ValueError as error:
        names = ", ".join(n.value for n in PeriodName)
        raise InvalidArguments(key, f"기간 이름은 다음 중 하나다: {names}") from error
    try:
        return PeriodSpec(
            name,
            days=_days(value, key) if name is PeriodName.LAST_N_DAYS else _days_absent(value),
            start=_month(value, key) or _date(value, "start", key),
            end=_date(value, "end", key),
        )
    except ValueError as error:
        raise InvalidArguments(key, str(error)) from error


def _days(value: Mapping[str, object], key: str) -> int:
    days = value.get("days")
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise InvalidArguments(key, "last_n_days에는 1 이상의 정수 days가 필요하다")
    return min(days, MAX_DAYS)  # 너무 긴 기간은 자른다. meta.periods에 실제 경계가 나간다


def _days_absent(value: Mapping[str, object]) -> int:
    days = value.get("days")
    return days if isinstance(days, int) and not isinstance(days, bool) else 0


def _month(value: Mapping[str, object], key: str) -> date | None:
    text = value.get("month")
    if text is None:
        return None
    match = _MONTH.match(text) if isinstance(text, str) else None
    if match is None:
        raise InvalidArguments(key, "month는 YYYY-MM이다")
    return date(int(match.group(1)), int(match.group(2)), 1)


def _date(value: Mapping[str, object], field: str, key: str) -> date | None:
    text = value.get(field)
    if text is None:
        return None
    hint = f"{field}는 YYYY-MM-DD다"
    if not isinstance(text, str):
        raise InvalidArguments(key, hint)
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise InvalidArguments(key, hint) from error


def _text(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidArguments(key, "문자열이어야 한다")
    return value.strip()[:_TEXT_LIMIT]


def _direction(raw: Mapping[str, object]) -> Direction | None:
    text = _text(raw, "direction")
    if not text:
        return None
    try:
        return Direction(text)
    except ValueError as error:
        raise InvalidArguments("direction", "expense나 income이다") from error
