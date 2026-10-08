from __future__ import annotations

from api.infrastructure.db import Base
from api.infrastructure.db.rows import DocumentRow

TABLE = Base.metadata.tables[DocumentRow.__tablename__]


def test_a_law_with_its_source_serial_and_effective_date():
    assert [c.name for c in TABLE.columns] == [
        "id",
        "title",
        "source",
        "mst",
        "effective_date",
        "body",
    ]
