from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """금액. 정수 최소단위(원)만 받는다. float가 섞이면 만드는 순간 죽는다.

    ui는 금액을 계산하지 않는다. 연산은 api 대역(infrastructure/memory)이 쓰고,
    화면은 표시만 한다. 음수도 받는다 — 예산 초과의 "남음", 지난달 대비 증감.
    """

    amount: int
    currency: str = "KRW"

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"금액은 정수 최소단위다: {self.amount!r}")

    @classmethod
    def total(cls, items: Iterable[Money]) -> Money:
        result = cls(0)
        for item in items:
            result = result + item
        return result

    def __add__(self, other: Money) -> Money:
        return Money(self.amount + self._same(other).amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        return Money(self.amount - self._same(other).amount, self.currency)

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def __bool__(self) -> bool:
        return self.amount != 0

    def __format__(self, spec: str) -> str:
        """`f"{money:,}"` → "8,500". 문구 조립이 금액을 풀어 쓰지 않게 한다."""
        return format(self.amount, spec)

    def _same(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise ValueError(f"통화가 다르다: {self.currency} / {other.currency}")
        return other
