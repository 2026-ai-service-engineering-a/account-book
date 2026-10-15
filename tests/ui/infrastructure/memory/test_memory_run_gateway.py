from __future__ import annotations

import asyncio

from ui.application.dto import RunFilter
from ui.application.values import RunId
from ui.infrastructure.memory import MemoryRunGateway


def test_the_stand_in_has_no_runs():
    gateway = MemoryRunGateway()
    page = asyncio.run(gateway.page(RunFilter()))
    assert page.items == () and page.next_cursor is None
    assert asyncio.run(gateway.get(RunId("r1"))) is None
