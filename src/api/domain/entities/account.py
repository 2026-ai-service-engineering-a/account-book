from __future__ import annotations

from dataclasses import dataclass

from api.domain.values import AccountId


@dataclass(frozen=True, slots=True)
class Account:
    id: AccountId
    name: str
    kind: str  # cash · card · bank
