from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RunCall:
    """실행 안의 도구 호출 하나. 인자와 결과는 저장된 JSON 그대로다 — 모양이 자리마다 다르다."""

    call_id: str
    tool: str
    args: Mapping[str, object]
    result: Mapping[str, object] | None  # 대기 중이거나 취소된 제안은 비어 있다
    confirmed_at: datetime | None  # 쓰기 제안만 — 사람이 확인한 시각
