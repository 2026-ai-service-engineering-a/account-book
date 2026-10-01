from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    """돈이 나갔나 들어왔나."""

    EXPENSE = "expense"
    INCOME = "income"
