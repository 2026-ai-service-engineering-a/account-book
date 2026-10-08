from __future__ import annotations

from agent.application.dto import ToolPrompt, Turn
from agent.domain.tools import Mode


def test_tools_are_the_seats_specs():
    prompt = ToolPrompt("query", "system", (Turn("user", "q"),), Mode.QUERY.specs())
    assert [s.name for s in prompt.tools] == list(Mode.QUERY.tools)
