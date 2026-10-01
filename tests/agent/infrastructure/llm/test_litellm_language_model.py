from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from agent.application.errors import MalformedOutput, ModelUnavailable
from agent.application.prompts import capture_prompt
from agent.infrastructure.llm import LitellmLanguageModel

PROMPT = capture_prompt("카페 5천원")


def reply(content: object) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def complete(monkeypatch: pytest.MonkeyPatch, outcome: object) -> dict[str, Any]:
    """litellm을 가짜로 바꿔 끼우고 한 번 부른다. 넘긴 인자를 돌려준다."""
    seen: dict[str, Any] = {}

    async def fake(**kwargs: Any) -> object:
        seen.update(kwargs)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(litellm, "acompletion", fake)
    model = LitellmLanguageModel("gemini/gemini-flash-lite-latest", "secret", timeout=3)
    seen["result"] = asyncio.run(model.complete_json(PROMPT))
    return seen


def test_returns_the_json_object(monkeypatch):
    seen = complete(monkeypatch, reply('{"amount": 5000}'))
    assert seen["result"] == {"amount": 5000}


def test_asks_for_the_schema_deterministically(monkeypatch):
    seen = complete(monkeypatch, reply("{}"))
    schema = seen["response_format"]["json_schema"]
    assert schema["name"] == "capture" and schema["schema"] is PROMPT.schema
    assert seen["temperature"] == 0 and seen["timeout"] == 3 and seen["api_key"] == "secret"
    assert [m["role"] for m in seen["messages"]] == ["system", "user"]


@pytest.mark.parametrize("content", ["not json", "[1, 2]", None])
def test_anything_but_an_object_is_malformed(monkeypatch, content):
    with pytest.raises(MalformedOutput):
        complete(monkeypatch, reply(content))


def test_empty_choices_is_malformed(monkeypatch):
    with pytest.raises(MalformedOutput):
        complete(monkeypatch, SimpleNamespace(choices=[]))


def test_provider_errors_become_unavailable(monkeypatch):
    with pytest.raises(ModelUnavailable, match="TimeoutError"):
        complete(monkeypatch, TimeoutError("slow"))
