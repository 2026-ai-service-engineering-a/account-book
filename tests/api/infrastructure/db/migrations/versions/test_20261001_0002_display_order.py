from __future__ import annotations

import pytest
from sqlalchemy import inspect

from tests.api.conftest import migrate

pytestmark = pytest.mark.integration


def test_adds_and_removes_position(database):
    migrate(database, "0002")
    assert "position" in {c["name"] for c in inspect(database).get_columns("categories")}
    migrate(database, "0001", down=True)
    assert "position" not in {c["name"] for c in inspect(database).get_columns("categories")}
