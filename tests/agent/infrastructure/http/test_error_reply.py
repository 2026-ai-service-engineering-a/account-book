from __future__ import annotations

from agent.infrastructure.http.error_reply import ErrorReply


def test_details_may_be_missing():
    reply = ErrorReply.model_validate({"error": {"code": "not_found", "message": "없다"}})
    assert reply.error["code"] == "not_found" and "details" not in reply.error
