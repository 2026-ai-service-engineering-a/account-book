from __future__ import annotations

from api.application.dto import SkippedCategory
from api.domain.values import CategoryId, SkipReason


def test_carries_the_reason():
    skipped = SkippedCategory(CategoryId("cafe"), SkipReason.SHORT_HISTORY)
    assert skipped.reason == "short_history"  # 값은 응답에 그대로 나가는 글자다
