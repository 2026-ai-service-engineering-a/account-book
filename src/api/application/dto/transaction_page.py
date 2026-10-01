from __future__ import annotations

from dataclasses import dataclass

from api.domain.entities import Transaction


@dataclass(frozen=True, slots=True)
class TransactionPage:
    items: tuple[Transaction, ...]
    next_cursor: str | None  # 없으면 마지막 쪽
