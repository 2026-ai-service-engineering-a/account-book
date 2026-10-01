from __future__ import annotations

import json

from api.interfaces.schemas import ErrorResponse


def test_same_envelope_for_every_error():
    response = ErrorResponse.reply(422, "validation_error", "m", {"amount": "금액"})
    assert response.status_code == 422
    assert json.loads(bytes(response.body)) == {
        "error": {"code": "validation_error", "message": "m", "details": {"amount": "금액"}}
    }
