from __future__ import annotations

from dataclasses import dataclass

from .transaction_line import TransactionLine


@dataclass(frozen=True, slots=True)
class TransactionList:
    """search_transactions의 답. 최근 것부터."""

    transactions: tuple[TransactionLine, ...]
    has_more: bool  # 더 있다 — 모델에게 기간을 좁히라고 알린다
