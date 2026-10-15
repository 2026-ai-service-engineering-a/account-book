from __future__ import annotations

from collections.abc import Mapping

from .ledger_unavailable import LedgerUnavailable


class LedgerRejected(LedgerUnavailable):
    """api가 4xx와 에러 코드로 거절했다. `code`로 가른다 — `message`는 파싱하지 않는다
    (api-contract 5장). 범위 밖이라는 판단도 api가 한다(docs/ai/mcp.md 5장)."""

    def __init__(self, status: int, code: str, details: Mapping[str, str]) -> None:
        super().__init__(f"{status} {code}")
        self.status = status
        self.code = code
        self.details = dict(details)
