from __future__ import annotations

import secrets
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, text

from api.infrastructure.settings import Settings

ALEMBIC_INI = Path(__file__).parents[2] / "src" / "api" / "alembic.ini"


class FixedProbe:
    def __init__(self, up: bool = True) -> None:
        self.up = up

    def ping(self) -> bool:
        return self.up


def migrate(engine: Engine, revision: str = "head", down: bool = False) -> None:
    """env.py가 이 연결로 돈다 — 개발용 DB가 아니라 테스트가 만든 DB다."""
    config = Config(str(ALEMBIC_INI))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        if down:
            command.downgrade(config, revision)
        else:
            command.upgrade(config, revision)


@pytest.fixture
def database() -> Iterator[Engine]:
    """테스트마다 빈 DB를 하나 만들고 끝나면 지운다. 개발용 DB의 데이터는 건드리지 않는다.

    compose의 db가 떠 있어야 한다(-m integration). 만드는 권한은 POSTGRES_USER에 있다.
    """
    settings = Settings()
    name = f"test_{secrets.token_hex(6)}"
    admin = create_engine(settings.database_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(settings.database_url(name))
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


@pytest.fixture
def migrated(database: Engine) -> Engine:
    migrate(database)
    return database
