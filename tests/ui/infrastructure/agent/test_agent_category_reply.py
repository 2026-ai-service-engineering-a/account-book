from __future__ import annotations

import pytest
from pydantic import ValidationError

from ui.infrastructure.agent import AgentCategoryReply


def test_llm_choice_is_marked():
    reply = AgentCategoryReply(category_id="food", strategy="llm", reason="배달앱이라 식비")
    suggestion = reply.suggestion()
    assert suggestion.category_id == "food" and suggestion.by_llm


def test_abstain_has_no_category():
    reply = AgentCategoryReply(category_id=None, strategy="none", reason="근거 없음")
    suggestion = reply.suggestion()
    assert suggestion.category_id is None and suggestion.reason == "근거 없음"


def test_rejects_unknown_strategy():
    with pytest.raises(ValidationError):
        AgentCategoryReply.model_validate(
            {"category_id": "food", "strategy": "guess", "reason": ""}
        )
