from __future__ import annotations

import logging

import pytest
from alembic import command
from alembic.config import Config

from tests.api.conftest import ALEMBIC_INI


def test_offline_sql_generation_is_refused():
    # 마이그레이션은 언제나 실제 DB에 대고 돈다. SQL 파일로 뽑는 길은 막아 둔다
    with pytest.raises(SystemExit, match="오프라인"):
        command.upgrade(Config(str(ALEMBIC_INI)), "head", sql=True)


def test_reading_the_logging_config_leaves_other_loggers_on():
    # alembic.ini의 로그 설정을 읽어도 이미 있는 로거는 그대로다 — 꺼지면 운영 로그가 사라진다
    other = logging.getLogger("tests.api.someone_else")
    with pytest.raises(SystemExit):
        command.upgrade(Config(str(ALEMBIC_INI)), "head", sql=True)
    assert not other.disabled


@pytest.mark.integration
def test_runs_on_the_connection_it_is_given(database):
    # 테스트가 만든 DB에 돈다 — 개발용 DB가 아니다
    config = Config(str(ALEMBIC_INI))
    with database.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with database.connect() as connection:
        assert connection.exec_driver_sql("SELECT version_num FROM alembic_version").scalar()
