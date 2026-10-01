from __future__ import annotations

from enum import StrEnum


class SearchStrategy(StrEnum):
    """api 검색이 어느 길로 답했나.

    rule·history는 결정적이라 그대로 쓰고, vector는 신뢰도를 본다.
    """

    RULE = "rule"
    HISTORY = "history"
    VECTOR = "vector"
    NONE = "none"
