from __future__ import annotations

from pathlib import Path

from api.application.use_cases import LoadDocuments, SearchDocuments
from api.domain.values import ChunkStrategy
from tests.api.conftest import FakeUnitOfWork

LAWS = Path(__file__).parents[3] / "fixtures" / "ai" / "documents" / "laws"


def library() -> FakeUnitOfWork:
    uow = FakeUnitOfWork()
    LoadDocuments(uow)(p.read_text(encoding="utf-8") for p in sorted(LAWS.glob("*.md")))
    return uow


def test_finds_the_clause_that_names_the_words():
    hits = SearchDocuments(library())("수영장 및 체력단련장", ChunkStrategy.PARAGRAPH)
    assert hits[0].chunk.id == "paragraph:조세특례제한법 시행령/제121조의2/16"
    assert hits[0].title == "조세특례제한법 시행령" and len(hits) == 5


def test_only_the_asked_strategy_and_k_is_kept_in_range():
    search = SearchDocuments(library())
    assert {h.chunk.strategy for h in search("카드", ChunkStrategy.FIXED_500, k=50)} == {
        ChunkStrategy.FIXED_500
    }
    assert len(search("카드", k=50)) == 20 and len(search("카드", k=0)) == 1


def test_blank_question_finds_nothing():
    assert SearchDocuments(library())("   ") == ()
