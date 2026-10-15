from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol


class InsightCache(Protocol):
    """리포트 AI 영역의 캐시(docs/ai/agentic-reports.md 8장). agent는 DB를 모르니 api에 둔다.

    닿지 못하면 `LedgerUnavailable` — 캐시는 가속기라 부르는 쪽이 삼키고 그냥 만든다.
    """

    async def get(self, key: str) -> Mapping[str, object] | None: ...

    async def put(self, key: str, body: Mapping[str, object]) -> None: ...
