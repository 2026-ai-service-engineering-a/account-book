from __future__ import annotations

from dataclasses import dataclass

from agent.domain.values import CategoryId, Direction, TimeRange


@dataclass(frozen=True, slots=True)
class TransactionFilter:
    """api의 거래 걸름 — 목록·합계·빈도가 같은 걸름을 쓴다(api-contract 6장).

    기간은 이미 풀린 경계다. `text`는 api의 `q` — 가맹점·메모에 든 글자.
    """

    period: TimeRange
    category_id: CategoryId | None = None
    text: str = ""
    direction: Direction | None = None
