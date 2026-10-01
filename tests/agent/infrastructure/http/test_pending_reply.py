from __future__ import annotations

from agent.application.dto import PendingText
from agent.infrastructure.http import PendingReply


def test_becomes_pending_texts():
    reply = PendingReply.model_validate({"items": [{"text_hash": "h", "text": "스타벅스"}]})
    assert reply.texts() == (PendingText("h", "스타벅스"),)
