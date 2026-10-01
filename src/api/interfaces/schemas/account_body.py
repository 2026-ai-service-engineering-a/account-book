from __future__ import annotations

from pydantic import BaseModel

from api.domain.entities import Account


class AccountBody(BaseModel):
    id: str
    name: str
    kind: str

    @classmethod
    def of(cls, account: Account) -> AccountBody:
        return cls(id=account.id, name=account.name, kind=account.kind)
