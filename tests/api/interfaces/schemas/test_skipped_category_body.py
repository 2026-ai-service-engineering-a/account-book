from __future__ import annotations

import pytest
from pydantic import ValidationError

from api.application.dto import SkippedCategory
from api.domain.values import CategoryId
from api.interfaces.schemas import SkippedCategoryBody


def test_only_the_two_reasons():
    body = SkippedCategoryBody.of(SkippedCategory(CategoryId("cafe"), "too_few"))
    assert body.model_dump() == {"category_id": "cafe", "reason": "too_few"}
    with pytest.raises(ValidationError):
        SkippedCategoryBody.of(SkippedCategory(CategoryId("cafe"), "dunno"))
