"""모델이 낸 도구 인자(JSON)를 domain/tools의 입력으로. `Any`(모양을 모르는 값)는 여기서 끝난다.

틀리면 `InvalidToolArguments(필드, 힌트)` — 실행기가 봉투(ok: false)로 바꿔 모델에게 돌려준다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date

from agent.application.errors import InvalidToolArguments
from agent.domain.tools import (
    DEFAULT_ROWS,
    MAX_ROWS,
    ComparePeriodsInput,
    CountFrequencyInput,
    GetBudgetStatusInput,
    SearchTransactionsInput,
    SuggestCategoryInput,
    SummarizeSpendingInput,
    ToolName,
)
from agent.domain.values import CategoryId, Direction, PeriodName, PeriodSpec
from agent.domain.values.period_spec import MAX_DAYS

type ToolInput = (
    SearchTransactionsInput
    | SummarizeSpendingInput
    | CountFrequencyInput
    | ComparePeriodsInput
    | GetBudgetStatusInput
    | SuggestCategoryInput
)

_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_PERIOD_KEYS = {"name", "days", "month", "start", "end"}
_TEXT_LIMIT = 100  # api의 q 상한
_KEYS: Mapping[ToolName, set[str]] = {
    ToolName.SEARCH_TRANSACTIONS: {"period", "category_id", "merchant", "direction", "limit"},
    ToolName.SUMMARIZE_SPENDING: {"period", "category_id", "merchant", "direction"},
    ToolName.COUNT_FREQUENCY: {"period", "category_id", "merchant", "direction"},
    ToolName.COMPARE_PERIODS: {"a", "b", "category_id"},
    ToolName.GET_BUDGET_STATUS: {"period", "category_id"},
    ToolName.SUGGEST_CATEGORY: {"merchant", "memo", "direction"},
}


def parse_tool_arguments(name: ToolName, raw: Mapping[str, object]) -> ToolInput:
    keys = _KEYS.get(name)
    if keys is None:
        raise InvalidToolArguments("name", f"{name}은 아직 부를 수 없는 도구다")
    unknown = sorted(set(raw) - keys)
    if unknown:
        accepted = ", ".join(sorted(keys))
        raise InvalidToolArguments(unknown[0], f"이 도구가 받지 않는 인자다. 받는 것: {accepted}")
    try:
        return _build(name, raw)
    except ValueError as error:  # 입력 dataclass가 스스로 막은 것
        raise InvalidToolArguments("arguments", str(error)) from error


def _build(name: ToolName, raw: Mapping[str, object]) -> ToolInput:
    match name:
        case ToolName.SEARCH_TRANSACTIONS:
            return SearchTransactionsInput(
                _period(raw, "period"),
                _category(raw),
                _text(raw, "merchant"),
                _direction(raw),
                _limit(raw),
            )
        case ToolName.SUMMARIZE_SPENDING:
            return SummarizeSpendingInput(
                _period(raw, "period"), _category(raw), _text(raw, "merchant"), _direction(raw)
            )
        case ToolName.COUNT_FREQUENCY:
            return CountFrequencyInput(
                _period(raw, "period"),
                _category(raw),
                _text(raw, "merchant"),
                _direction(raw) or Direction.EXPENSE,
            )
        case ToolName.COMPARE_PERIODS:
            return ComparePeriodsInput(_period(raw, "a"), _period(raw, "b"), _category(raw))
        case ToolName.GET_BUDGET_STATUS:
            return GetBudgetStatusInput(_period(raw, "period"), _category(raw))
        case _:
            return SuggestCategoryInput(
                _text(raw, "merchant"),
                _text(raw, "memo"),
                _direction(raw) or Direction.EXPENSE,
            )


def _period(raw: Mapping[str, object], key: str) -> PeriodSpec:
    value = raw.get(key)
    if isinstance(value, str):  # 이름만 넘긴 것 — 표의 `period=last_week` 모양도 받는다
        value = {"name": value}
    if not isinstance(value, Mapping):
        raise InvalidToolArguments(key, "기간은 {'name': 기간 이름} 모양이어야 한다")
    unknown = sorted(set(value) - _PERIOD_KEYS)
    if unknown:
        raise InvalidToolArguments(key, f"기간이 받지 않는 값이다: {unknown[0]}")
    try:
        name = PeriodName(str(value.get("name")))
    except ValueError as error:
        names = ", ".join(n.value for n in PeriodName)
        raise InvalidToolArguments(key, f"기간 이름은 다음 중 하나다: {names}") from error
    try:
        return PeriodSpec(
            name,
            days=_days(value, key) if name is PeriodName.LAST_N_DAYS else _days_absent(value),
            start=_month(value, key) or _date(value, "start", key),
            end=_date(value, "end", key),
        )
    except ValueError as error:
        raise InvalidToolArguments(key, str(error)) from error


def _days(value: Mapping[str, object], key: str) -> int:
    days = value.get("days")
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise InvalidToolArguments(key, "last_n_days에는 1 이상의 정수 days가 필요하다")
    return min(days, MAX_DAYS)  # 너무 긴 기간은 자른다. 답에 기간을 밝히므로 드러난다


def _days_absent(value: Mapping[str, object]) -> int:
    days = value.get("days")
    return days if isinstance(days, int) and not isinstance(days, bool) else 0


def _month(value: Mapping[str, object], key: str) -> date | None:
    text = value.get("month")
    if text is None:
        return None
    match = _MONTH.match(text) if isinstance(text, str) else None
    if match is None:
        raise InvalidToolArguments(key, "month는 YYYY-MM이다")
    return date(int(match.group(1)), int(match.group(2)), 1)


def _date(value: Mapping[str, object], field: str, key: str) -> date | None:
    text = value.get(field)
    if text is None:
        return None
    hint = f"{field}는 YYYY-MM-DD다 — 질문에 적힌 날짜를 그대로 옮긴다"
    if not isinstance(text, str):
        raise InvalidToolArguments(key, hint)
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise InvalidToolArguments(key, hint) from error


def _category(raw: Mapping[str, object]) -> CategoryId | None:
    text = _text(raw, "category_id")
    return CategoryId(text) if text else None


def _text(raw: Mapping[str, object], key: str) -> str:
    value = raw.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidToolArguments(key, "문자열이어야 한다")
    return value.strip()[:_TEXT_LIMIT]


def _direction(raw: Mapping[str, object]) -> Direction | None:
    text = _text(raw, "direction")
    if not text:
        return None
    try:
        return Direction(text)
    except ValueError as error:
        raise InvalidToolArguments("direction", "expense나 income이다") from error


def _limit(raw: Mapping[str, object]) -> int:
    value = raw.get("limit")
    if value is None:
        return DEFAULT_ROWS
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise InvalidToolArguments("limit", f"1~{MAX_ROWS}의 정수다")
    return min(value, MAX_ROWS)
