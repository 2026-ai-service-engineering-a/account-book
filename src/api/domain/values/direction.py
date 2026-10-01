from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    """돈이 나갔나 들어왔나. 카테고리 목록이 여기에 딸린다."""

    EXPENSE = "expense"
    INCOME = "income"
