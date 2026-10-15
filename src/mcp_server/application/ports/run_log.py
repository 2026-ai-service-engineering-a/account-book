from __future__ import annotations

from typing import Protocol

from mcp_server.application.dto import RunEntry


class RunLog(Protocol):
    """감사 로그. 실패하면 `LedgerUnavailable` — 부르는 쪽이 삼키고 답은 낸다."""

    async def record(self, entry: RunEntry) -> None: ...
