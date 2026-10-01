from __future__ import annotations

import json
from collections.abc import Mapping

import litellm

from agent.application.dto import Prompt
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
