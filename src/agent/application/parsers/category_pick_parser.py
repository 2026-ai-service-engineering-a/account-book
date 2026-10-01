"""LLM이 낸 카테고리 선택 JSON을 `CategoryPick`으로. 모양만 본다 — 근거 검사는 유스케이스가 한다."""

from __future__ import annotations

from collections.abc import Mapping

from agent.application.dto import CategoryPick
from agent.application.errors import MalformedOutput
from agent.domain.values import CategoryId


def parse_category_pick(raw: Mapping[str, object]) -> CategoryPick:
    category = raw.get("category_id")
    evidence = raw.get("evidence_ids")
    reason = raw.get("reason")
    abstain = raw.get("abstain")
    confidence = raw.get("self_confidence")
    if not isinstance(category, str):
        raise MalformedOutput("category_id가 문자열이 아니다")
    if not isinstance(evidence, list) or not all(isinstance(e, str) for e in evidence):
        raise MalformedOutput("evidence_ids가 문자열 목록이 아니다")
    if not isinstance(reason, str):
        raise MalformedOutput("reason이 문자열이 아니다")
    if not isinstance(abstain, bool):
        raise MalformedOutput("abstain이 참거짓이 아니다")
    if isinstance(confidence, bool) or not isinstance(confidence, int | float):
        raise MalformedOutput("self_confidence가 숫자가 아니다")
    return CategoryPick(
        category_id=CategoryId(category) if category else None,
        evidence_ids=tuple(evidence),
        reason=reason.strip(),
        abstain=abstain,
        self_confidence=float(confidence),
    )
