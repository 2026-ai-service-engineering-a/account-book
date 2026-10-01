from __future__ import annotations

from agent.domain.values import CategoryChoice
from agent.interfaces.schemas import CategoryChoiceBody


def test_abstain_is_a_null_category():
    body = CategoryChoiceBody.of(CategoryChoice.abstain("근거가 없어요")).model_dump()
    assert body == {"category_id": None, "strategy": "none", "reason": "근거가 없어요"}
