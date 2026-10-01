from __future__ import annotations

import secrets
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import Engine, create_engine, text

from api.application.ports import DatabaseProbe, UnitOfWork
from api.infrastructure.settings import Settings
from api.main import create_app

# 가짜들은 fakes.py에 있다. 테스트들이 여기서 가져다 쓰던 이름을 그대로 내보낸다.
from tests.api.fakes import SEOUL as SEOUL
from tests.api.fakes import FakeBudgets as FakeBudgets
from tests.api.fakes import FakeCatalog as FakeCatalog
from tests.api.fakes import FakeIdempotency as FakeIdempotency
from tests.api.fakes import FakeStats as FakeStats
from tests.api.fakes import FakeTransactions as FakeTransactions
from tests.api.fakes import FakeUnitOfWork as FakeUnitOfWork
from tests.api.fakes import FixedClock as FixedClock
from tests.api.fakes import FixedProbe as FixedProbe
from tests.api.fakes import draft as draft

ALEMBIC_INI = Path(__file__).parents[2] / "src" / "api" / "alembic.ini"


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


def client_with(
    uow: Callable[[], UnitOfWork] | None = None, database: DatabaseProbe | None = None
) -> TestClient:
    """가짜 작업 단위로 조립한 api. 비밀번호는 쓰지 않지만 설정이 요구한다."""
    settings = Settings(_env_file=None, postgres_password=SecretStr("unused"))
    app = create_app(
        settings, database=database or FixedProbe(), unit_of_work=uow or FakeUnitOfWork()
    )
    return TestClient(app, raise_server_exceptions=False)
