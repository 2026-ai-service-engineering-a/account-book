from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import TypeAdapter, ValidationError

from ui.application.dto import Account, Category, Direction
from ui.application.errors import LedgerUnavailable
from ui.application.values import AccountId, CategoryId

from .api_client import ApiClient


# 응답 모양. 이 게이트웨이만 쓰는 TypedDict라 같은 파일에 둔다(development-rules 1.2의 예외).
class _CategoryItem(TypedDict):
    id: str
    name: str
    direction: Literal["expense", "income"]


class _AccountItem(TypedDict):
    id: str
    name: str


_CATEGORIES = TypeAdapter(list[_CategoryItem])
_ACCOUNTS = TypeAdapter(list[_AccountItem])


class HttpCatalogGateway:
    """카테고리와 결제수단 — api의 `/v1/categories`, `/v1/accounts`."""

    def __init__(self, client: ApiClient) -> None:
        self._client = client

    async def categories(self, direction: Direction | None = None) -> tuple[Category, ...]:
        params: dict[str, str | int] = {"direction": direction.value} if direction else {}
        response = await self._client.request("GET", "/v1/categories", params=params)
        try:
            items = _CATEGORIES.validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
        return tuple(
            Category(CategoryId(i["id"]), i["name"], Direction(i["direction"])) for i in items
        )

    async def accounts(self) -> tuple[Account, ...]:
        response = await self._client.request("GET", "/v1/accounts")
        try:
            items = _ACCOUNTS.validate_json(response.content)
        except ValidationError as error:
            raise LedgerUnavailable("모르는 응답 모양") from error
        return tuple(Account(AccountId(i["id"]), i["name"]) for i in items)
