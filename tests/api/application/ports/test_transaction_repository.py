from __future__ import annotations

from api.application.ports import TransactionRepository
from tests.api.conftest import FakeTransactions


def test_fake_fills_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: TransactionRepository = FakeTransactions()
    assert port is not None
