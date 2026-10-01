from __future__ import annotations


class InvalidTransaction(Exception):
    """거래가 규칙에 맞지 않는다. 422 validation_error.

    `details`는 필드 이름 → 사람이 읽을 문구다. 화면이 해당 필드 옆에만 표시한다.
    """

    def __init__(self, details: dict[str, str]) -> None:
        super().__init__("validation_error")
        self.details = details
