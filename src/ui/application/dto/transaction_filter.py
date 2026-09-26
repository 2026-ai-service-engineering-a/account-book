from __future__ import annotations

from dataclasses import dataclass

from .direction import Direction
from .period import Period


@dataclass(frozen=True, slots=True)
class TransactionFilter:
    period: Period
    direction: Direction | None = None
    category_id: str | None = None
    query: str = ""

    @property
    def is_narrowed(self) -> bool:
        """기간 말고 다른 조건이 걸려 있나. 빈 화면 문구가 여기서 갈린다."""
        return bool(self.direction or self.category_id or self.query)
