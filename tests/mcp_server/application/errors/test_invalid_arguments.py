from __future__ import annotations

from mcp_server.application.errors import InvalidArguments


def test_keeps_the_field_and_the_hint_for_the_model():
    error = InvalidArguments("period", "기간 이름은 다음 중 하나다")
    assert (error.field, error.hint) == ("period", "기간 이름은 다음 중 하나다")
