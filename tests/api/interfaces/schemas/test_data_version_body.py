from __future__ import annotations

from api.interfaces.schemas import DataVersionBody


def test_an_opaque_string():
    assert DataVersionBody(version="3f2a").model_dump() == {"version": "3f2a"}
