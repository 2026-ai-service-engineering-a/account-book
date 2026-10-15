from __future__ import annotations

import httpx

from agent.application.errors import LedgerRejected
from agent.infrastructure.http.error_reply import ErrorReply


def test_details_may_be_missing():
    reply = ErrorReply.model_validate({"error": {"code": "not_found", "message": "없다"}})
    assert reply.error["code"] == "not_found" and "details" not in reply.error


def test_rejection_reads_the_code_and_falls_back_on_an_unknown_shape():
    known = httpx.Response(412, json={"error": {"code": "confirmation_required", "message": "x"}})
    rejected = ErrorReply.rejection(known)
    assert isinstance(rejected, LedgerRejected) and rejected.code == "confirmation_required"
    unknown = ErrorReply.rejection(httpx.Response(400, text="?"))
    assert not isinstance(unknown, LedgerRejected)
