from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class InsightCache(Protocol):
    """리포트 AI 영역의 캐시(docs/ai/agentic-reports.md 8장). 키가 버전이라 TTL이 없다.

    api는 안을 읽지 않는다 — 모양은 agent가 정한다.
    """

    def get(self, key: str) -> Mapping[str, object] | None: ...

    def put(self, key: str, body: Mapping[str, object]) -> None:
        """있으면 갈아 끼운다. 커밋은 부르는 쪽(멱등 쓰기)이 한다."""
        ...
