from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Amount:
    """집계가 낸 금액. 정수 최소단위(원)와 통화를 함께 다닌다(ai/tools.md 3.2).

    `Money`는 거래 한 건이라 0보다 커야 하지만, 합계는 0일 수 있고 증감은 음수일 수 있다.
    서식("8,500원")은 화면의 일이라 여기서 만들지 않는다.
    """

    amount: int
    currency: str = "KRW"

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"금액은 정수 최소단위다: {self.amount!r}")
