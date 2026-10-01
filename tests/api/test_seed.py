from __future__ import annotations

import pytest

from api import seed

pytestmark = pytest.mark.integration


def test_seeds_the_configured_database(monkeypatch, migrated):
    # Settings가 가리키는 DB 대신 테스트가 만든 DB로 돌린다
    monkeypatch.setattr(seed, "create_db_engine", lambda _url: migrated)
    assert seed.main() == 11
