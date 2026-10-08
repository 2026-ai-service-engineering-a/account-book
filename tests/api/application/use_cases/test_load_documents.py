from __future__ import annotations

from pathlib import Path

import pytest

from api.application.use_cases import LoadDocuments
from api.domain.values import ChunkStrategy
from tests.api.conftest import FakeUnitOfWork

LAWS = Path(__file__).parents[3] / "fixtures" / "ai" / "documents" / "laws"


def texts() -> list[str]:
    return [p.read_text(encoding="utf-8") for p in sorted(LAWS.glob("*.md"))]


def test_six_laws_into_three_strategies():
    uow = FakeUnitOfWork()
    counts = LoadDocuments(uow)(texts())
    assert counts == {
        ChunkStrategy.FIXED_500: 51,
        ChunkStrategy.PARAGRAPH: 77,
        ChunkStrategy.PARAGRAPH_ITEM: 104,
    }
    assert len(uow.documents.documents) == 6 and len(uow.documents.chunks) == 232
    assert uow.commits == 1


def test_loading_twice_changes_nothing():
    uow = FakeUnitOfWork()
    LoadDocuments(uow)(texts())
    before = dict(uow.documents.chunks)
    LoadDocuments(uow)(texts())
    assert uow.documents.chunks == before


def test_one_unreadable_law_and_nothing_goes_in():
    uow = FakeUnitOfWork()
    with pytest.raises(ValueError):
        LoadDocuments(uow)([*texts(), "# 머리가 없는 법\n"])
    assert uow.documents.chunks == {} and uow.commits == 0
