from __future__ import annotations

from api.interfaces.schemas import ErrorBody


def test_details_are_optional():
    assert ErrorBody(code="not_found", message="m").details is None
