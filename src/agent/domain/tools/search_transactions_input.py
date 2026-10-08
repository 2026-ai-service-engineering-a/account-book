from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Direction, PeriodSpec

DEFAULT_ROWS = 20
MAX_ROWS = 50  # 계약의 페이지 상한(200)보다 좁게 — 모델이 200행을 읽을 이유는 거의 없다


@dataclass(frozen=True, slots=True)
class SearchTransactionsInput:
    period: PeriodSpec
    category_id: CategoryId | None = None
    merchant: str = ""  # 가맹점·메모에 든 글자(부분 일치)
    direction: Direction | None = None
    limit: int = DEFAULT_ROWS

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= MAX_ROWS:
            raise ValueError(f"limit은 1~{MAX_ROWS}다: {self.limit}")
