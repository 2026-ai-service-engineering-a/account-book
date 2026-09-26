from __future__ import annotations


class LedgerValidationError(Exception):
    """api의 `validation_error`. `details`를 받아 해당 필드 옆에만 표시한다."""

    def __init__(self, details: dict[str, str]) -> None:
        super().__init__("validation_error")
        self.details = details
