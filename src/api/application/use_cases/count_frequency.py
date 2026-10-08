from __future__ import annotations

from collections.abc import Callable

from api.application.dto import Frequency, TransactionQuery
from api.application.ports import UnitOfWork
from api.domain.values import CategoryId, Direction, TimeRange


class CountFrequency:
    """기간 안 건수와 거래가 있던 날 수 — `count_frequency` 도구의 자리(api-contract 6장).

    걸름은 `summarize_spending`과 같다. 목록·합계와 다른 거래를 세지 않는다. 방향의 기본이
    지출인 것만 다르다 — 수입과 지출을 섞으면 회당 평균이 아무 뜻도 없다.
    """

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(
        self,
        period: TimeRange,
        direction: Direction = Direction.EXPENSE,
        category_id: CategoryId | None = None,
        text: str = "",
    ) -> Frequency:
        query = TransactionQuery(
            start=period.start,
            end=period.end,
            direction=direction,
            category_id=category_id,
            text=text.strip(),
        )
        with self._unit_of_work() as uow:
            return uow.stats.frequency(query)
