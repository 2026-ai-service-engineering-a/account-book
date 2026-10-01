from __future__ import annotations

from datetime import UTC, datetime

import pytest

from api import seed

pytestmark = pytest.mark.integration
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


def test_reference_only_by_default(monkeypatch, migrated):
    # Settings가 가리키는 DB 대신 테스트가 만든 DB로 돌린다
    monkeypatch.setattr(seed, "create_db_engine", lambda _url: migrated)
    assert seed.main([], now=NOW) == 11


def test_demo_adds_example_transactions_once(monkeypatch, migrated):
    monkeypatch.setattr(seed, "create_db_engine", lambda _url: migrated)
    assert seed.main(["--demo"], now=NOW) > 11
    assert seed.main(["--demo"], now=NOW) == 11  # 이미 거래가 있으면 예시를 넣지 않는다
