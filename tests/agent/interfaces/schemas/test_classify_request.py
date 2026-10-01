from __future__ import annotations

import pytest
from pydantic import ValidationError

from agent.domain.values import Direction
from agent.interfaces.schemas import ClassifyRequest


def test_direction_value():
    assert ClassifyRequest(direction="income").direction_value() is Direction.INCOME


def test_rejects_long_merchant():
    with pytest.raises(ValidationError):
        ClassifyRequest(direction="expense", merchant="가" * 101)
