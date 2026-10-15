from __future__ import annotations

from enum import StrEnum


class Direction(StrEnum):
    """지출인가 수입인가. api의 `direction` 값과 같다."""

    EXPENSE = "expense"
    INCOME = "income"
