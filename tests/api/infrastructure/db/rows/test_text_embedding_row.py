from __future__ import annotations

from pgvector.sqlalchemy import Vector

from api.infrastructure.db import Base
from api.infrastructure.db.rows import EMBEDDING_DIMENSIONS, TextEmbeddingRow

TABLE = Base.metadata.tables[TextEmbeddingRow.__tablename__]


def test_one_vector_per_model_and_text():
    assert [c.name for c in TABLE.primary_key.columns] == ["model", "text_hash"]


def test_vector_is_768_with_a_cosine_hnsw_index():
    # agent의 EMBEDDING_DIMENSIONS와 같아야 하고, HNSW는 2000차원까지 받는다
    vector = TABLE.c.vector.type
    assert isinstance(vector, Vector) and vector.dim == EMBEDDING_DIMENSIONS == 768
    (index,) = TABLE.indexes
    options = index.dialect_options["postgresql"]
    assert options["using"] == "hnsw" and options["ops"] == {"vector": "vector_cosine_ops"}
