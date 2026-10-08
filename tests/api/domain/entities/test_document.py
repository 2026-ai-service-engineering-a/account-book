from __future__ import annotations

import dataclasses
from datetime import date

from api.domain.entities import Document
from api.domain.values import DocumentId


def test_a_frozen_law():
    law = Document(
        DocumentId("소득세법"), "소득세법", "국가법령정보센터", "280405", date(2026, 7, 1), ""
    )
    assert law.effective_date == date(2026, 7, 1)
    assert Document.__dataclass_params__.frozen  # type: ignore[attr-defined]  # 공개 API가 아니다
    assert [f.name for f in dataclasses.fields(Document)][:2] == ["id", "title"]
