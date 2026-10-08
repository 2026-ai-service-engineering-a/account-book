from __future__ import annotations

from api.infrastructure.db import Base
from api.infrastructure.db.rows import DocumentChunkRow

TABLE = Base.metadata.tables[DocumentChunkRow.__tablename__]


def test_columns_and_the_owning_document():
    assert [c.name for c in TABLE.columns] == [
        "id",
        "document_id",
        "strategy",
        "heading",
        "body",
        "search_text",
        "text_hash",
        "position",
    ]
    (foreign,) = TABLE.c.document_id.foreign_keys
    assert foreign.column.table.name == "documents" and foreign.ondelete == "CASCADE"


def test_search_text_has_a_trigram_index():
    index = next(i for i in TABLE.indexes if i.name == "ix_document_chunks_search_text")
    options = index.dialect_options["postgresql"]
    assert options["using"] == "gin" and options["ops"] == {"search_text": "gin_trgm_ops"}
