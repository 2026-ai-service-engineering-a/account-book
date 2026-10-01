from __future__ import annotations

from collections.abc import Callable

from api.application.dto import IndexText
from api.application.ports import UnitOfWork

MAX_PENDING = 200


class ListPendingTexts:
    """색인 안 된 텍스트 — agent가 당겨 가서 임베딩한다. api는 agent를 부르지 않는다(4.3)."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work = unit_of_work

    def __call__(self, model: str, limit: int) -> tuple[IndexText, ...]:
        with self._unit_of_work() as uow:
            return uow.index.pending(model, max(1, min(limit, MAX_PENDING)))
