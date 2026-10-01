from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from api.domain.values import CategoryId, Direction


@dataclass(frozen=True, slots=True)
class TransactionQuery:
    """거래 목록 조회. 기간은 이미 UTC 경계로 풀려 있다 — `[start, end)`.

    `cursor`는 저장소가 낸 불투명한 문자열이다. 여기서는 풀어 보지 않는다.
    """

    start: datetime | None = None
    end: datetime | None = None
    direction: Direction | None = None
    category_id: CategoryId | None = None
    text: str = ""
    cursor: str | None = None
    limit: int = 50
