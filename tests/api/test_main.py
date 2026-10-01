from __future__ import annotations

from api.infrastructure.db import SqlDatabaseProbe
from api.infrastructure.settings import Settings
from api.main import create_app


def test_assembles_a_real_probe_without_connecting(monkeypatch):
    # 엔진은 처음 쓸 때 연결한다 — 조립만으로는 DB에 닿지 않는다
    monkeypatch.setenv("POSTGRES_PASSWORD", "x")
    app = create_app(Settings(_env_file=None))
    assert isinstance(app.state.services.database, SqlDatabaseProbe)
