from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """금액. 정수 최소단위(원)만 받는다. float가 섞이면 만드는 순간 죽는다.

    음수도 받는다 — 집계의 증감과 예산의 "남음"이 음수가 될 수 있다. 거래 한 건의 금액이
    0보다 커야 한다는 규칙은 거래 쪽에 있다.
    """

    amount: int

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"금액은 정수 최소단위다: {self.amount!r}")

    @classmethod
    def total(cls, items: Iterable[Money]) -> Money:
        return cls(sum(item.amount for item in items))

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - other.amount)
