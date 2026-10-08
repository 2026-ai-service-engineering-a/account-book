from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from agent.application.dto import ModelUsage, ToolCall, ToolPrompt, Turn
from agent.application.errors import MalformedOutput, ModelUnavailable
from agent.application.prompts import capture_prompt
from agent.domain.tools import Mode
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


TOOL_PROMPT = ToolPrompt(
    "query",
    "도구를 골라라",
    (
        Turn("user", "저번 주 카페 몇 번?"),
        Turn("assistant", tool_calls=(ToolCall("c1", "count_frequency", {"period": "last_week"}),)),
        Turn("tool", '{"ok": true}', call_id="c1"),
    ),
    Mode.QUERY.specs(),
)


def tool_reply(content: object, calls: list[object] | None = None) -> SimpleNamespace:
    message = SimpleNamespace(content=content, tool_calls=calls)
    usage = SimpleNamespace(prompt_tokens=120, completion_tokens=12)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=usage)


def call(call_id: str, name: str, arguments: str) -> SimpleNamespace:
    return SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))


def choose(
    monkeypatch: pytest.MonkeyPatch, outcome: object, cost: object = 0.0002
) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    async def fake(**kwargs: Any) -> object:
        seen.update(kwargs)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def fake_cost(**_: Any) -> float:
        if isinstance(cost, Exception):
            raise cost
        assert isinstance(cost, float)
        return cost

    monkeypatch.setattr(litellm, "acompletion", fake)
    monkeypatch.setattr(litellm, "completion_cost", fake_cost)
    model = LitellmLanguageModel("gemini/gemini-flash-lite-latest", "secret", timeout=3)
    seen["result"] = asyncio.run(model.complete_with_tools(TOOL_PROMPT))
    return seen


def test_offers_the_seats_tools_and_replays_the_conversation(monkeypatch):
    seen = choose(monkeypatch, tool_reply("끝"))
    assert [t["function"]["name"] for t in seen["tools"]] == [t.value for t in Mode.QUERY.tools]
    first = seen["tools"][0]["function"]
    assert first["description"].count("\n") == 1  # 무엇을 / 언제 쓰지 않는가
    assert seen["tool_choice"] == "auto" and seen["temperature"] == 0
    roles = [m["role"] for m in seen["messages"]]
    assert roles == ["system", "user", "assistant", "tool"]
    assistant, tool = seen["messages"][2], seen["messages"][3]
    assert assistant["tool_calls"][0]["function"]["arguments"] == '{"period": "last_week"}'
    assert tool == {"role": "tool", "tool_call_id": "c1", "content": '{"ok": true}'}


def test_tool_calls_come_back_with_their_arguments_parsed(monkeypatch):
    raw = call("x1", "count_frequency", '{"period": {"name": "last_week"}, "category_id": "cafe"}')
    reply = choose(monkeypatch, tool_reply(None, [raw]))["result"]
    assert reply.tool_calls == (
        ToolCall("x1", "count_frequency", {"period": {"name": "last_week"}, "category_id": "cafe"}),
    )
    assert reply.text == ""
    assert reply.usage == ModelUsage(120, 12, 0.0002)


def test_text_without_tools_is_the_answer(monkeypatch):
    reply = choose(monkeypatch, tool_reply("  카페 3번이에요. "))["result"]
    assert reply.text == "카페 3번이에요." and reply.tool_calls == ()


def test_unknown_price_means_zero_cost_not_a_failure(monkeypatch):
    reply = choose(monkeypatch, tool_reply("끝"), cost=ValueError("no price"))["result"]
    assert reply.usage.cost_usd == 0.0 and reply.usage.input_tokens == 120


@pytest.mark.parametrize("arguments", ["not json", "[1]"])
def test_arguments_that_are_not_an_object_are_malformed(monkeypatch, arguments):
    with pytest.raises(MalformedOutput):
        choose(monkeypatch, tool_reply(None, [call("x1", "count_frequency", arguments)]))


def test_provider_errors_are_unavailable_for_tools_too(monkeypatch):
    with pytest.raises(ModelUnavailable):
        choose(monkeypatch, ConnectionError("down"))
