from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.ui.infrastructure.api.conftest import TX
from ui.application.dto import Source
from ui.application.values import Money
from ui.infrastructure.api import TransactionReply


def test_becomes_a_ui_transaction():
    transaction = TransactionReply.model_validate(TX).transaction()
    assert transaction.amount == Money(8500) and transaction.source is Source.AGENT


@pytest.mark.parametrize("broken", [{"amount": 0}, {"occurred_at": "2026-09-16T03:30:00"}])
def test_rejects_what_the_contract_rules_out(broken):
    with pytest.raises(ValidationError):
        TransactionReply.model_validate(TX | broken)
