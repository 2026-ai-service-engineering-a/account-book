from __future__ import annotations

from agent.application.dto import ModelReply, ModelUsage


def test_text_without_tools_is_an_answer():
    reply = ModelReply("카페 3번이에요.", (), ModelUsage())
    assert reply.tool_calls == ()
