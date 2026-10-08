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


def test_keyword_search_with_pg_trgm(migrated):
    laws = sorted(LAW.parent.glob("*.md"))
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        for path in laws:
            document = parse_law(path.read_text(encoding="utf-8"))
            uow.documents.replace(document, chunk_law(document, ChunkStrategy.PARAGRAPH))
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        hits = uow.documents.search("수영장 및 체력단련장", ChunkStrategy.PARAGRAPH, 5)
        none = uow.documents.search("수영장", ChunkStrategy.FIXED_500, 5)
    assert hits[0].chunk.id == "paragraph:조세특례제한법 시행령/제121조의2/16"
    assert hits[0].score > hits[-1].score and len(hits) == 5
    assert hits[0].title == "조세특례제한법 시행령"
    assert none == ()  # 그 전략의 조각은 넣지 않았다


def test_pending_chunk_texts_until_embedded(migrated):
    document = parse_law(LAW.read_text(encoding="utf-8"))
    chunks = chunk_law(document, ChunkStrategy.PARAGRAPH)
    sessions = SqlUnitOfWork.factory(migrated)
    with SqlUnitOfWork(sessions) as uow:
        uow.documents.replace(document, chunks)
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        pending = uow.documents.pending("m@768", 100)
        assert {p.text_hash for p in pending} == {c.text_hash for c in chunks}
        uow.index.put_embedding("m@768", pending[0].text_hash, tuple([0.1] * 768))
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        assert len(uow.documents.pending("m@768", 100)) == len(chunks) - 1


def test_nearest_by_cosine_through_text_embeddings(migrated):
    document = parse_law(LAW.read_text(encoding="utf-8"))
    chunks = chunk_law(document, ChunkStrategy.PARAGRAPH)
    sessions = SqlUnitOfWork.factory(migrated)

    def unit(i: int) -> tuple[float, ...]:
        return tuple(1.0 if j == i else 0.0 for j in range(768))

    with SqlUnitOfWork(sessions) as uow:
        uow.documents.replace(document, chunks)
        for i, chunk in enumerate(chunks):
            uow.index.put_embedding("m@768", chunk.text_hash, unit(i))
        uow.commit()
    with SqlUnitOfWork(sessions) as uow:
        hits = uow.documents.nearest(unit(3), "m@768", ChunkStrategy.PARAGRAPH, 2)
        other = uow.documents.nearest(unit(3), "other@768", ChunkStrategy.PARAGRAPH, 2)
    assert hits[0].chunk.id == chunks[3].id and hits[0].score == pytest.approx(1.0)
    assert hits[1].score == pytest.approx(0.0) and other == ()
