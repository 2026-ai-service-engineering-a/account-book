from __future__ import annotations

from collections.abc import Callable, Mapping

from api.application.ports import UnitOfWork


class ReadInsightCache:
    """캐시된 리포트 AI 영역. 없으면 None — agent가 만든다."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, key: str) -> Mapping[str, object] | None:
        with self._unit_of_work() as uow:
            return uow.insight_cache.get(key)
