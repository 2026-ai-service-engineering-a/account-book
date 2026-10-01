from __future__ import annotations


class InvalidEmbedding(Exception):
    """벡터의 차원이 맞지 않는다. 422 validation_error — 다른 모델이나 차원으로 임베딩한 것이다."""

    def __init__(self, details: dict[str, str]) -> None:
        super().__init__("validation_error")
        self.details = details
