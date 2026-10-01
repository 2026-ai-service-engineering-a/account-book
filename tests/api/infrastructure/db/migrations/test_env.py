from __future__ import annotations

import pytest
from alembic import command
from alembic.config import Config

from tests.api.conftest import ALEMBIC_INI


def test_offline_sql_generation_is_refused():
    # 마이그레이션은 언제나 실제 DB에 대고 돈다. SQL 파일로 뽑는 길은 막아 둔다
    with pytest.raises(SystemExit, match="오프라인"):
        command.upgrade(Config(str(ALEMBIC_INI)), "head", sql=True)


@pytest.mark.integration
def test_runs_on_the_connection_it_is_given(database):
    # 테스트가 만든 DB에 돈다 — 개발용 DB가 아니다
    config = Config(str(ALEMBIC_INI))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with database.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
