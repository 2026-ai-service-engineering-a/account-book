from __future__ import annotations

import json
from collections.abc import Mapping

import litellm

from agent.application.dto import ModelReply, ModelUsage, Prompt, ToolCall, ToolPrompt, Turn
from agent.application.errors import MalformedOutput, ModelUnavailable

# 실패할 때마다 "Give Feedback / Get Help" 안내를 stderr에 찍는다. 운영 로그가 지저분해진다.
litellm.suppress_debug_info = True


class LitellmLanguageModel:
    """litellm으로 제공자 하나를 부른다. Gemini·OpenAI·Anthropic이 같은 길을 지난다.

    스텁 없는 라이브러리의 반환값은 `Any`다. 여기서 JSON 객체로 바꾸고, 안쪽으로는
    `Mapping[str, object]`만 내보낸다(development-rules 5.2).
    """

    def __init__(self, model: str, api_key: str, timeout: float) -> None:
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        try:
            response = await litellm.acompletion(
                model=self._model,
                messages=[
                    {"role": "system", "content": prompt.system},
                    {"role": "user", "content": prompt.user},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": prompt.name, "schema": prompt.schema, "strict": True},
                },
                temperature=0,
                timeout=self._timeout,
                api_key=self._api_key,
            )
        # litellm은 제공자마다 다른 예외를 낸다(인증·한도·타임아웃·네트워크). 어느 것이든
        # 다시 시켜도 같은 답이라, 전부 한 가지로 번역한다. 원인은 체인에 남는다.
        except Exception as error:
            raise ModelUnavailable(type(error).__name__) from error
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError) as error:
            raise MalformedOutput("답에 내용이 없다") from error
        return _json_object(content)

    async def complete_with_tools(self, prompt: ToolPrompt) -> ModelReply:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": spec.name.value,
                    "description": spec.description,
                    "parameters": dict(spec.input_schema),
                },
            }
            for spec in prompt.tools
        ]
        messages: list[dict[str, object]] = [{"role": "system", "content": prompt.system}]
        messages += [_message(turn) for turn in prompt.turns]
        try:
            response = await litellm.acompletion(
                model=self._model,
                messages=messages,
                tools=tools or None,
                tool_choice="auto" if tools else None,
                temperature=0,
                timeout=self._timeout,
                api_key=self._api_key,
            )
        except Exception as error:  # complete_json과 같은 이유로 한 가지로 번역한다
            raise ModelUnavailable(type(error).__name__) from error
        try:
            message = response.choices[0].message
        except (AttributeError, IndexError) as error:
            raise MalformedOutput("답에 내용이 없다") from error
        calls = tuple(_tool_call(c) for c in (getattr(message, "tool_calls", None) or ()))
        text = message.content if isinstance(message.content, str) else ""
        return ModelReply(text=text.strip(), tool_calls=calls, usage=_usage(response))


def _message(turn: Turn) -> dict[str, object]:
    if turn.role == "tool":
        return {"role": "tool", "tool_call_id": turn.call_id, "content": turn.text}
    if turn.role == "assistant" and turn.tool_calls:
        return {
            "role": "assistant",
            "content": turn.text or None,
            "tool_calls": [
                {
                    "id": c.call_id,
                    "type": "function",
                    "function": {"name": c.name, "arguments": json.dumps(dict(c.arguments))},
                }
                for c in turn.tool_calls
            ],
        }
    return {"role": turn.role, "content": turn.text}


def _tool_call(raw: object) -> ToolCall:
    """제공자의 도구 호출 하나를 우리 타입으로. 인자는 JSON 글이라 여기서 푼다."""
    function = getattr(raw, "function", None)
    name = getattr(function, "name", None)
    arguments = getattr(function, "arguments", None)
    call_id = getattr(raw, "id", None)
    if not isinstance(name, str) or not isinstance(call_id, str):
        raise MalformedOutput("도구 이름이나 id가 글이 아니다")
    return ToolCall(call_id, name, _json_object(arguments or "{}"))


def _usage(response: object) -> ModelUsage:
    usage = getattr(response, "usage", None)
    try:
        cost = float(litellm.completion_cost(completion_response=response))
    # 값표에 없는 모델이면 litellm이 예외를 낸다. 비용 상한은 못 보지만 스텝 상한은 남는다
    except Exception:
        cost = 0.0
    return ModelUsage(
        input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
        cost_usd=cost,
    )


def _json_object(content: object) -> Mapping[str, object]:
    if not isinstance(content, str):
        raise MalformedOutput("답이 글이 아니다")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as error:
        raise MalformedOutput("답이 JSON이 아니다") from error
    if not isinstance(parsed, dict):
        raise MalformedOutput("답이 JSON 객체가 아니다")
    return parsed
