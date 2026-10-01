from __future__ import annotations

from ui.application.errors import LedgerUnavailable, LedgerValidationError


def test_is_not_a_validation_error():
    # 고칠 필드가 없다 — 화면은 에러 페이지로 옮긴다
    assert not issubclass(LedgerUnavailable, LedgerValidationError)
