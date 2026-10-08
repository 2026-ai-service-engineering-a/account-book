from __future__ import annotations

from agent.application.errors import LedgerRejected, LedgerUnavailable


def test_carries_the_code_and_is_still_a_ledger_failure():
    error = LedgerRejected(422, "validation_error", {"to": "끝"})
    assert (error.status, error.code, error.details) == (422, "validation_error", {"to": "끝"})
    assert isinstance(error, LedgerUnavailable)  # 분류·기록은 하나로 다룬다
