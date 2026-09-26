from __future__ import annotations

from dataclasses import dataclass

from ui.application.values import AccountId


@dataclass(frozen=True, slots=True)
class Account:
    """결제수단. 카드·현금·계좌이체."""

    id: AccountId
    name: str
