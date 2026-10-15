"""계획 호출(LLM 1)이 낸 JSON을 `PlanStep`들로. `Any`(모양을 모르는 값)는 여기서 끝난다.

인자는 JSON 문자열로 받는다 — 도구마다 모양이 다른 객체는 엄격한 구조화 출력 스키마로
적을 수 없다. 문자열이 JSON 객체가 아니면 그 단계의 인자만 None으로 두고, 단계를 버리는
것은 검사(plan_check)가 한다. 계획 전체의 모양이 틀렸을 때만 `MalformedOutput`이다.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from agent.application.dto import PlanStep
from agent.application.errors import MalformedOutput

_WHY_LIMIT = 200


def parse_plan(raw: Mapping[str, object]) -> tuple[PlanStep, ...]:
    steps = raw.get("steps")
    if not isinstance(steps, list):
        raise MalformedOutput("steps가 목록이 아니다")
    out: list[PlanStep] = []
    for step in steps:
        if not isinstance(step, Mapping):
            raise MalformedOutput("단계가 객체가 아니다")
        tool, args, why = step.get("tool"), step.get("args"), step.get("why")
        if not isinstance(tool, str) or not isinstance(args, str) or not isinstance(why, str):
            raise MalformedOutput("단계는 tool·args·why 글이다")
        out.append(PlanStep(tool.strip(), _object(args), why.strip()[:_WHY_LIMIT]))
    return tuple(out)


def _object(text: str) -> Mapping[str, object] | None:
    try:
        value = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
