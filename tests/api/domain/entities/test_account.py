from __future__ import annotations

from api.domain.entities import Account
from api.domain.values import AccountId


def test_has_a_kind():
    assert Account(AccountId("card"), "카드", "card").kind == "card"
