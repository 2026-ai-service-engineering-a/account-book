from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.domain.values import Money
from api.interfaces.schemas import TransactionWrite
from tests.api.interfaces.test_write_headers import BODY


def test_becomes_a_draft():
    assert TransactionWrite.model_validate(BODY).draft().amount == Money(8500)


@pytest.mark.parametrize(
    "broken",
    [{"amount": "8500"}, {"amount": 8500.0}, {"occurred_at": "2026-09-16T12:30:00"}],
)
def test_strict_shapes(broken):
    # 금액은 정수 원, 시각은 aware — 그 밖은 받지 않는다
    with pytest.raises(ValidationError):
        TransactionWrite.model_validate(BODY | broken)
