from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredReply:
    """쓰기 요청 하나의 응답. 멱등 키와 함께 저장했다가 같은 요청이 다시 오면 그대로 돌려준다."""

    status_code: int
    body: Mapping[str, object] | None = None
