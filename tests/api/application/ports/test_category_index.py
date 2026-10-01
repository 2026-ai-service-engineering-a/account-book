from __future__ import annotations

from api.application.ports import CategoryIndex
from tests.api.conftest import FakeTransactions
from tests.api.fake_index import FakeIndex


def test_fake_fills_the_port():
    port: CategoryIndex = FakeIndex(FakeTransactions())
    assert port is not None
