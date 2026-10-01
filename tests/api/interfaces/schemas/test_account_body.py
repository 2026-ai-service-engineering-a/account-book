from __future__ import annotations

from api.domain.entities import Account
from api.domain.values import AccountId
from api.interfaces.schemas import AccountBody


def test_shape():
    body = AccountBody.of(Account(AccountId("card"), "카드", "card"))
    assert body.model_dump() == {"id": "card", "name": "카드", "kind": "card"}
