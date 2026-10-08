from __future__ import annotations

from collections.abc import Mapping

from .ledger_unavailable import LedgerUnavailable


class LedgerRejected(LedgerUnavailable):
    """api가 4xx와 에러 코드로 거절했다. `code`로 가른다 — `message`는 파싱하지 않는다
    (api-contract 5장).

    `LedgerUnavailable`의 하위형이다. 실패를 하나로 다루는 자리(분류·기록)는 그대로 두고,
    도구 실행기만 코드를 보고 모델이 고칠 수 있는 실패를 가른다(ai/tools.md 5장).
    """

    def __init__(self, status: int, code: str, details: Mapping[str, str]) -> None:
        super().__init__(f"{status} {code}")
        self.status = status
        self.code = code
        self.details = dict(details)
