"""도구 출력(domain/tools의 dataclass)을 JSON 모양으로, 그리고 크기 상한(ai/tools.md 3.2).

금액은 정수 최소단위와 통화를 함께 낸다. "8,500원" 같은 문자열을 만들지 않는다 — 서식은
화면의 일이다.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum

from agent.domain.values import Amount, Confidence

MAX_BYTES = 8 * 1024  # 직렬화가 이보다 크면 목록의 뒤부터 자른다


def plain(value: object) -> object:
    """dataclass·값 객체·날짜를 JSON에 들어갈 값으로."""
    if isinstance(value, Amount):
        return {"amount": value.amount, "currency": value.currency}
    if isinstance(value, Confidence):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple | list):
        return [plain(item) for item in value]
    if isinstance(value, Mapping):
        return {str(k): plain(v) for k, v in value.items()}
    return value


def fit(data: dict[str, object], rows_key: str) -> bool:
    """`data[rows_key]` 목록의 뒤부터 덜어 8KB 안에 넣는다. 덜었으면 True."""
    rows = data.get(rows_key)
    if not isinstance(rows, list):
        return False
    trimmed = False
    while rows and _size(data) > MAX_BYTES:
        rows.pop()
        trimmed = True
    return trimmed


def _size(data: Mapping[str, object]) -> int:
    return len(json.dumps(data, ensure_ascii=False).encode())
