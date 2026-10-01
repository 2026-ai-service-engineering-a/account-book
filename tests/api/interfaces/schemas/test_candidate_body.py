from __future__ import annotations

from api.interfaces.schemas import CandidateBody


def test_shape():
    assert CandidateBody(category_id="cafe", confidence=0.5).confidence == 0.5
