"""결과의 크기 상한(docs/ai/tools.md 3.2). 외부라고 더 주지 않는다(docs/ai/mcp.md 7.1)."""

from __future__ import annotations

import json
from collections.abc import Mapping

MAX_BYTES = 8 * 1024  # 직렬화가 이보다 크면 목록의 뒤부터 자른다


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
