"""조립 지점. 어느 구현이 어느 포트를 채우는지는 여기서만 정한다.

    uvicorn api.main:create_app --factory --port 8000

스키마는 뜨기 전에 alembic이 올린다(Dockerfile, docker-compose.dev.yml).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from zoneinfo import ZoneInfo

from fastapi import FastAPI

from api.application.ports import DatabaseProbe, UnitOfWork
from api.application.use_cases import (
    CreateTransaction,
    DeleteTransaction,
    GetTransaction,
    IdempotentWrite,
    ListCatalog,
    SearchTransactions,
    UpdateTransaction,
)
from api.domain.values import Money
from api.infrastructure.db import SqlDatabaseProbe, create_db_engine
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork
from api.infrastructure.settings import Settings
from api.interfaces.services import Services
from api.interfaces.web_app import build_web_app


def create_app(
    settings: Settings | None = None,
    database: DatabaseProbe | None = None,
    unit_of_work: Callable[[], UnitOfWork] | None = None,
) -> FastAPI:
    """가짜를 넘기면 그것을 쓴다. 엔진은 처음 쓸 때 연결한다 — 조립만으로는 DB에 닿지 않는다."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = settings or Settings()
    if database is None or unit_of_work is None:
        engine = create_db_engine(settings.database_url())
        sessions = SqlUnitOfWork.factory(engine)

        def sql_unit_of_work() -> UnitOfWork:
            return SqlUnitOfWork(sessions)

        database = database or SqlDatabaseProbe(engine)
        unit_of_work = unit_of_work or sql_unit_of_work
    threshold = Money(settings.agent_confirm_threshold)
    zone = ZoneInfo(settings.user_timezone)
    return build_web_app(
        Services(
            database=database,
            write=IdempotentWrite(unit_of_work),
            create=CreateTransaction(threshold),
            update=UpdateTransaction(threshold),
            delete=DeleteTransaction(),
            get=GetTransaction(unit_of_work),
            search=SearchTransactions(unit_of_work, zone),
            catalog=ListCatalog(unit_of_work),
        )
    )
