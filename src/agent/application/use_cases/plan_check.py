"""계획의 단계를 검사한다(docs/ai/agent-loop.md 5.1의 표). 걸린 단계만 버린다.

| 도구가 그 모드의 목록에 있나 | 버린다 |
| 인자가 스키마에 맞나         | 버린다 |
| 같은 (도구, 인자)가 중복인가 | 하나만 남긴다 — 이미 부른 것(고정 호출·앞 계획)과도 |
| 단계 수가 상한을 넘나        | 앞에서부터 상한까지만 |

남은 단계가 0개인지는 부르는 쪽이 본다. 실행은 코드가 한다 — 여기서 LLM을 부르지 않는다.
"""

from __future__ import annotations

import json
from collections.abc import Collection, Iterable

from agent.application.dto import PlanStep, ToolCall
from agent.application.errors import InvalidToolArguments
from agent.application.parsers import parse_tool_arguments
from agent.domain.tools import ToolName


def checked_plan(
    steps: Iterable[PlanStep],
    offered: Collection[ToolName],
    called: Iterable[ToolCall],
    limit: int,
    first_number: int,
) -> tuple[tuple[ToolCall, PlanStep], ...]:
    """살아남은 단계를 부를 호출로. call_id는 `call_{first_number}`부터 이어 붙인다."""
    seen = {_key(c.name, c.arguments) for c in called}
    kept: list[tuple[ToolCall, PlanStep]] = []
    for step in steps:
        if len(kept) >= limit:
            break
        tool = next((t for t in offered if t.value == step.tool), None)
        if tool is None or step.arguments is None:
            continue
        try:
            parse_tool_arguments(tool, step.arguments)
        except InvalidToolArguments:
            continue
        key = _key(step.tool, step.arguments)
        if key in seen:
            continue
        seen.add(key)
        call_id = f"call_{first_number + len(kept)}"
        kept.append((ToolCall(call_id, step.tool, dict(step.arguments)), step))
    return tuple(kept)


def _key(name: str, arguments: object) -> tuple[str, str]:
    return name, json.dumps(arguments, sort_keys=True, ensure_ascii=False)
