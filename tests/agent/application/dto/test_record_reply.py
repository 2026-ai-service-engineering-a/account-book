from __future__ import annotations

from agent.application.dto import RecordReply


def test_a_plain_message_is_not_an_error_and_wrote_nothing():
    reply = RecordReply(text="취소했어요.")
    assert not reply.code and not reply.wrote and reply.card is None
