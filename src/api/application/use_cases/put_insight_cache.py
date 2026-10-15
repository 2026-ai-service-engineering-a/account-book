from __future__ import annotations

from collections.abc import Mapping

from api.application.ports import UnitOfWork


class PutInsightCache:
    """리포트 AI 영역을 캐시에 넣는다. 커밋은 부르는 쪽(멱등 쓰기)이 한다."""

    def __call__(self, uow: UnitOfWork, key: str, body: Mapping[str, object]) -> None:
        uow.insight_cache.put(key, body)
