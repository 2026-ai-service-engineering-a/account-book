from __future__ import annotations

from api.infrastructure.db import Base


def test_constraints_get_predictable_names():
    # 이름이 없으면 DB가 지어 붙이고, 마이그레이션에서 지울 때 찾을 수 없다
    assert Base.metadata.naming_convention["ck"] == "ck_%(table_name)s_%(constraint_name)s"
