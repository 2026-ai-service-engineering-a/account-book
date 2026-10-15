from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .rows import InsightCacheRow


class SqlInsightCache:
    """리포트 캐시를 Postgres에. 같은 키면 갈아 끼운다 — 모델이 같은 입력에 다르게 답해도
    마지막 것이 남는다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, key: str) -> Mapping[str, object] | None:
        row = self._session.get(InsightCacheRow, key)
        return dict(row.body) if row is not None else None

    def put(self, key: str, body: Mapping[str, object]) -> None:
        statement = insert(InsightCacheRow).values(key=key, body=dict(body))
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[InsightCacheRow.key], set_={"body": statement.excluded.body}
            )
        )
