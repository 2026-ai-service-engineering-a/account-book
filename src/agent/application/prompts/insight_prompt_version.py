"""리포트 프롬프트의 버전 — 캐시 키의 prompt_version(docs/ai/agentic-reports.md 8장).

프롬프트·스키마·도구 설명을 해시한다. 손으로 올리는 번호가 아니다 — 고치고 잊어도 옛 결과가
나오지 않는다. 옛 결과가 나오면 평가를 믿을 수 없다.
"""

from __future__ import annotations

import hashlib
import json

from agent.domain.tools import Mode

from .insight_assembly_prompt import INSIGHT_SCHEMA
from .insight_assembly_prompt import SYSTEM as ASSEMBLY_SYSTEM
from .insight_plan_prompt import PLAN_SCHEMA
from .insight_plan_prompt import SYSTEM as PLAN_SYSTEM


def insight_prompt_version() -> str:
    tools = [(s.name.value, s.description, s.input_schema) for s in Mode.INSIGHT.specs()]
    material = json.dumps(
        [PLAN_SYSTEM, PLAN_SCHEMA, ASSEMBLY_SYSTEM, INSIGHT_SCHEMA, tools],
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(material.encode()).hexdigest()[:12]
