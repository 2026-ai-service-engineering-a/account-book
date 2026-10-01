from __future__ import annotations

from dataclasses import dataclass

# 한 건에 백억 원을 넘는 가계부 기록은 없다. 넘으면 읽기가 틀린 것이다.
_CEILING = 10_000_000_000


@dataclass(frozen=True, slots=True)
class Money:
    """거래 한 건의 금액. 정수 최소단위(원), 0보다 크다. float가 섞이면 만드는 순간 죽는다."""

    amount: int
    currency: str = "KRW"

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"금액은 정수 최소단위다: {self.amount!r}")
        if not 0 < self.amount <= _CEILING:
            raise ValueError(f"거래 금액의 범위를 벗어났다: {self.amount}")
