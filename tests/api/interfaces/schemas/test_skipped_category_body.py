from __future__ import annotations

from api.application.dto import SkippedCategory
from api.domain.values import CategoryId, SkipReason
from api.interfaces.schemas import SkippedCategoryBody


def test_the_reason_goes_out_as_its_value():
    body = SkippedCategoryBody.of(SkippedCategory(CategoryId("cafe"), SkipReason.TOO_FEW))
    assert body.model_dump(mode="json") == {"category_id": "cafe", "reason": "too_few"}
