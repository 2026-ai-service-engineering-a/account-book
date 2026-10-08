from __future__ import annotations

from api.domain.values import DocumentId


def test_is_the_law_name():
    assert DocumentId("조세특례제한법") == "조세특례제한법"
