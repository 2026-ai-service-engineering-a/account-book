""" "눈에 띈 것" 문장을 검사한다(docs/ai/agentic-reports.md 6·7장). 버리는 단위는 문장 하나다.

- 숫자는 이번 실행의 도구 결과에 있는 것만 — 기능 2의 대조(number_check)를 그대로 쓴다.
- 훈계하지 않는다 — 금지어 목록으로 검사한다. 프롬프트에 적어만 두면 언젠가 새어 나온다.
- 세 줄까지.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date

from agent.application.dto import HighlightDraft, ToolStep

from .number_check import numbers_from_tools, unsupported

MAX_HIGHLIGHTS = 3
# 사람을 꾸짖거나 무엇을 하라고 시키는 말. 가계부는 판단할 근거만 준다(6장의 4번)
SCOLDING = (
    "아껴",
    "아끼",
    "절약",
    "과소비",
    "낭비",
    "줄이세요",
    "줄여야",
    "줄이는 게",
    "자제",
    "조심",
    "주의하세요",
    "하셔야",
    "해야 합니다",
)


def kept_highlights(
    drafts: Iterable[HighlightDraft], steps: Iterable[ToolStep], today: date
) -> tuple[str, ...]:
    allowed = numbers_from_tools(steps, today)
    kept: list[str] = []
    for draft in drafts:
        if len(kept) >= MAX_HIGHLIGHTS:
            break
        text = draft.text
        if not text or any(word in text for word in SCOLDING):
            continue
        if unsupported(text, allowed):
            continue
        kept.append(text)
    return tuple(kept)
