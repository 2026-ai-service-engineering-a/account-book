from __future__ import annotations

import pytest

from api.application.use_cases import PutEmbedding
from api.domain.errors import InvalidEmbedding
from tests.api.conftest import FakeUnitOfWork


def test_stores_a_768_dimension_vector():
    uow = FakeUnitOfWork()
    PutEmbedding()(uow, "m", "h", tuple([0.1] * 768))
    assert uow.index.stored_vector("m", "h") is not None


def test_refuses_the_wrong_dimension():
    with pytest.raises(InvalidEmbedding, match="validation_error"):
        PutEmbedding()(FakeUnitOfWork(), "m", "h", (0.1, 0.2))
