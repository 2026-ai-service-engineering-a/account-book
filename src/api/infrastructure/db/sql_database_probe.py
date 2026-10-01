from __future__ import annotations

import logging

from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

_log = logging.getLogger(__name__)


class SqlDatabaseProbe:
    """`SELECT 1` 한 번. sqlalchemy 예외는 여기서 끝난다 — 라우터는 참거짓만 받는다."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def ping(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            # 처리하는 곳이 여기라 한 번만 남긴다. 접속 주소에는 비밀번호가 있어 남기지 않는다
            _log.warning("db ping failed: %s", type(error).__name__)
            return False
        return True
