"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

    uvicorn api.main:create_app --factory --port 8000

스키마는 뜨기 전에 alembic이 올린다(Dockerfile, docker-compose.dev.yml).
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from api.application.ports import DatabaseProbe
from api.infrastructure.db import SqlDatabaseProbe, create_db_engine
from api.infrastructure.settings import Settings
from api.interfaces.services import Services
from api.interfaces.web_app import build_web_app


def create_app(settings: Settings | None = None, database: DatabaseProbe | None = None) -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    if database is None:
        engine = create_db_engine((settings or Settings()).database_url())
        database = SqlDatabaseProbe(engine)
    return build_web_app(Services(database=database))
