from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Account:
    """결제수단. 카드·현금·계좌이체."""

    id: str
    name: str
