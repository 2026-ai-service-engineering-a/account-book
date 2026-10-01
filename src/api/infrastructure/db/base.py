from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# 제약 이름을 정해 둔다. 이름이 없으면 DB가 지어 붙이고, 마이그레이션에서 지울 때 찾을 수 없다.
_NAMING = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """테이블 매핑의 바탕. 매핑 클래스는 `rows/`에 테이블 하나씩 있다."""

    metadata = MetaData(naming_convention=_NAMING)
