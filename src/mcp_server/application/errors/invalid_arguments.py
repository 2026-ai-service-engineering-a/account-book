from __future__ import annotations


class InvalidArguments(Exception):
    """바깥 모델이 넘긴 인자가 계약에 맞지 않는다. 모델이 고칠 수 있는 실패다.

    `hint`는 우리가 쓰는 문장이고 결과의 오류 플래그와 함께 모델에게 간다(docs/ai/tools.md 5장).
    """

    def __init__(self, field: str, hint: str) -> None:
        super().__init__(f"{field}: {hint}")
        self.field = field
        self.hint = hint
