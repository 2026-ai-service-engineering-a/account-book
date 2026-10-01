from __future__ import annotations

from agent.interfaces.schemas import ErrorResponse


def test_same_envelope_as_the_api():
    body = ErrorResponse.of("model_unavailable", "지금은 안 돼요").model_dump()
    assert body == {"error": {"code": "model_unavailable", "message": "지금은 안 돼요"}}
