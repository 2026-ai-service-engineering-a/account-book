from __future__ import annotations

from agent.interfaces.schemas import ErrorBody


def test_code_and_message():
    assert ErrorBody(code="model_unavailable", message="m").code == "model_unavailable"
