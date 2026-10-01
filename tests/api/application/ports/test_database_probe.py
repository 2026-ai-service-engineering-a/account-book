from __future__ import annotations

from sqlalchemy import create_engine

from api.application.ports import DatabaseProbe
from api.infrastructure.db import SqlDatabaseProbe
from tests.api.conftest import FixedProbe


def test_sql_probe_and_fake_fill_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    real: DatabaseProbe = SqlDatabaseProbe(create_engine("sqlite://"))
    fake: DatabaseProbe = FixedProbe()
    assert callable(real.ping) and fake.ping()
