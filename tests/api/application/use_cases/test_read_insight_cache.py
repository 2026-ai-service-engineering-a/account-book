from __future__ import annotations

from api.application.use_cases import ReadInsightCache
from tests.api.conftest import FakeUnitOfWork


def test_nothing_cached_is_none():
    assert ReadInsightCache(FakeUnitOfWork())("a" * 64) is None
