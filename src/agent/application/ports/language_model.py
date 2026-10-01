from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from agent.application.dto import Prompt


class LanguageModel(Protocol):
    """구조화 출력을 내는 LLM. 어느 제공자인지는 조립 지점만 안다."""

    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        """`prompt.schema` 모양의 JSON 객체 하나를 낸다.

        JSON이 아니면 `MalformedOutput`, 제공자에 닿지 못하면 `ModelUnavailable`.
        키 하나하나의 검사는 부르는 쪽이 한다 — 어댑터는 모양을 모른다.
        """
        ...
