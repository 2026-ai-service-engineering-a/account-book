from __future__ import annotations

import asyncio

import pytest

from tests.ui.infrastructure.api.conftest import client, recorder
from ui.application.dto import Direction
from ui.application.errors import LedgerUnavailable
from ui.application.ports import CatalogGateway
from ui.infrastructure.api import HttpCatalogGateway


def test_fills_the_port_and_reads_categories():
    handler, seen = recorder(body=[{"id": "salary", "name": "급여", "direction": "income"}])
    port: CatalogGateway = HttpCatalogGateway(client(handler))
    categories = asyncio.run(port.categories(Direction.INCOME))
    assert seen[0].url.params["direction"] == "income"
    assert categories[0].name == "급여" and categories[0].direction is Direction.INCOME


def test_accounts():
    handler, _ = recorder(body=[{"id": "card", "name": "카드", "kind": "card"}])
    assert asyncio.run(HttpCatalogGateway(client(handler)).accounts())[0].id == "card"


def test_strange_body_is_unavailable():
    handler, _ = recorder(body={"not": "a list"})
    with pytest.raises(LedgerUnavailable):
        asyncio.run(HttpCatalogGateway(client(handler)).accounts())
