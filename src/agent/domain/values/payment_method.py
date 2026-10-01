from __future__ import annotations

from enum import StrEnum


class PaymentMethod(StrEnum):
    """결제수단의 종류. README 7장 `accounts.kind`와 같은 셋이다."""

    CARD = "card"
    CASH = "cash"
    BANK = "bank"
