from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from sqlalchemy import Engine, func, select

from api.domain.rules.law_chunking import chunk_law
from api.domain.rules.law_markdown import parse_law
from api.domain.values import ChunkStrategy
from api.infrastructure.db.rows import DocumentChunkRow, DocumentRow
from api.infrastructure.db.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration
LAW = Path(__file__).parents[3] / "fixtures" / "ai" / "documents" / "laws" / "income-tax-act.md"


def count(engine: Engine, row: type[DocumentRow] | type[DocumentChunkRow]) -> int:
    with engine.connect() as connection:
        return connection.execute(select(func.count()).select_from(row)).scalar_one()


def test_replace_swaps_the_chunks_and_keeps_one_document(migrated):
    document = parse_law(LAW.read_text(encoding="utf-8"))
    chunks = [c for s in ChunkStrategy for c in chunk_law(document, s)]
    sessions = SqlUnitOfWork.factory(migrated)
    for _ in range(2):
        with SqlUnitOfWork(sessions) as uow:
            uow.documents.replace(document, chunks)
            uow.commit()
    assert count(migrated, DocumentRow) == 1 and count(migrated, DocumentChunkRow) == len(chunks)
    # 청킹이 바뀌어 조각이 줄면 옛 조각이 남지 않는다
    newer = dataclasses.replace(document, mst="999")
    with SqlUnitOfWork(sessions) as uow:
        uow.documents.replace(newer, chunks[:3])
        uow.commit()
    assert count(migrated, DocumentChunkRow) == 3
    with migrated.connect() as connection:
        assert connection.execute(select(DocumentRow.mst)).scalar_one() == "999"
