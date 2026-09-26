from __future__ import annotations

from ui.application.errors import LedgerValidationError


def test_keeps_field_details():
    error = LedgerValidationError({"amount": "금액은 0보다 커야 합니다."})
    assert error.details == {"amount": "금액은 0보다 커야 합니다."}
    assert str(error) == "validation_error"  # 메시지에 값을 싣지 않는다
