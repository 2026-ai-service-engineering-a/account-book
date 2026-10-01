from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL


def create_db_engine(url: URL) -> Engine:
    """연결 풀을 가진 엔진 하나. 서비스가 뜰 때 한 번 만들고 끝까지 쓴다.

    `pool_pre_ping` — DB가 재시작된 뒤 죽은 연결을 집어 첫 요청이 실패하는 일을 막는다.
    """
    return create_engine(url, pool_pre_ping=True)
