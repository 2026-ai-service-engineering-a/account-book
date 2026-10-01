from __future__ import annotations

from sqlalchemy.engine import URL

from api.infrastructure.db import create_db_engine


def test_pings_before_reusing_a_pooled_connection():
    engine = create_db_engine(URL.create("postgresql+psycopg", host="db", database="x"))
    assert engine.pool._pre_ping  # DB가 재시작된 뒤 죽은 연결을 집지 않는다
