from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.interfaces.schemas import EmbeddingBody


def test_needs_a_model_and_a_vector():
    with pytest.raises(ValidationError):
        EmbeddingBody(model="", vector=[0.1])
    with pytest.raises(ValidationError):
        EmbeddingBody(model="m", vector=[])
