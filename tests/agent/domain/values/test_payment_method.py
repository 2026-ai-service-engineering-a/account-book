from __future__ import annotations

from agent.domain.values import PaymentMethod


def test_same_three_as_account_kinds():
    assert {p.value for p in PaymentMethod} == {"card", "cash", "bank"}
