from __future__ import annotations


class InvalidToolArguments(Exception):
    """모델이 넘긴 도구 인자가 스키마에 맞지 않는다. 모델이 고칠 수 있는 실패다.

    `hint`는 우리가 쓰는 문장이고 모델에게 간다(ai/tools.md 5장).
    """

    def __init__(self, field: str, hint: str) -> None:
        super().__init__(f"{field}: {hint}")
        self.field = field
        self.hint = hint
