from __future__ import annotations

from api.application.use_cases import PutInsightCache, ReadInsightCache
from tests.api.conftest import FakeUnitOfWork


def test_put_leaves_the_commit_to_the_caller():
    uow = FakeUnitOfWork()
    with uow:
        PutInsightCache()(uow, "k", {"highlights": []})
    assert ReadInsightCache(uow)("k") is None  # 커밋하지 않아 되돌아갔다
    with uow:
        PutInsightCache()(uow, "k", {"highlights": []})
        uow.commit()
    assert ReadInsightCache(uow)("k") == {"highlights": []}
