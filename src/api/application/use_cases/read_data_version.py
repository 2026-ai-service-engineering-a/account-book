from __future__ import annotations

from collections.abc import Callable

from api.application.ports import UnitOfWork
from api.domain.values import TimeRange


class ReadDataVersion:
    """기간 거래와 예산의 버전. 리포트 캐시가 "데이터가 바뀌었나"를 이것으로 안다 — 시간이
    지났는지가 아니다(agentic-reports 8장). 어떤 기간을 볼지는 부르는 쪽이 정한다."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, period: TimeRange) -> str:
        with self._unit_of_work() as uow:
            return uow.stats.data_version(period.start, period.end)
