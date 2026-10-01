from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.domain.values import Money
from api.interfaces.schemas import BudgetWrite


def test_null_clears():
    assert BudgetWrite(limit_amount=None).amount() is None
    assert BudgetWrite(limit_amount=5).amount() == Money(5)


def test_strict_integer():
    with pytest.raises(ValidationError):
        BudgetWrite.model_validate({"limit_amount": "5만원"})
