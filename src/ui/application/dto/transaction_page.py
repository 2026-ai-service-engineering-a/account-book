from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import PageCursor

from .transaction import Transaction


@dataclass(frozen=True, slots=True)
class TransactionPage:
    items: tuple[Transaction, ...]
    next_cursor: PageCursor | None  # 없으면 마지막 쪽
