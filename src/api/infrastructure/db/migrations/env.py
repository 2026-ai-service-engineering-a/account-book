"""alembic이 마이그레이션마다 실행하는 파일. 접속은 Settings에서 읽는다.

테스트는 `config.attributes["connection"]`에 연결을 넣어 따로 만든 DB에 돌린다.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import Connection

from api.infrastructure.db import Base, create_db_engine
from api.infrastructure.db import rows as _rows  # noqa: F401 — 매핑이 메타데이터에 올라온다
from api.infrastructure.settings import Settings

config = context.config
if config.config_file_name is not None and not config.attributes.get("connection"):
    fileConfig(config.config_file_name)


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def _online() -> None:
    given: Connection | None = config.attributes.get("connection")
    if given is not None:
        _run(given)
        return
    with create_db_engine(Settings().database_url()).connect() as connection:
        _run(connection)


if context.is_offline_mode():
    # SQL 파일로 뽑는 길은 쓰지 않는다. 마이그레이션은 언제나 실제 DB에 대고 돈다.
    raise SystemExit("오프라인 모드는 쓰지 않는다 — DB에 대고 upgrade한다")
_online()
