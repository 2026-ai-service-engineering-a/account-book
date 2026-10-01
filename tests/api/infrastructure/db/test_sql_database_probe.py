from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from api.infrastructure.db import SqlDatabaseProbe


def test_unreachable_database_is_false_not_an_exception():
    # 닿지 않는 주소 — sqlalchemy 예외가 라우터까지 올라가지 않는다
    url = URL.create("postgresql+psycopg", host="127.0.0.1", port=1, database="x")
    engine = create_engine(url, connect_args={"connect_timeout": 1})
    assert SqlDatabaseProbe(engine).ping() is False


@pytest.mark.integration
def test_real_database_is_true(database):
    assert SqlDatabaseProbe(database).ping() is True
