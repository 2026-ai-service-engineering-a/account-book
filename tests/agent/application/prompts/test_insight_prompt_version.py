from __future__ import annotations

import importlib

from agent.application.prompts import insight_prompt_version

# 패키지가 같은 이름의 함수를 내보낸다 — 모듈은 이름으로 따로 꺼낸다
MODULE = importlib.import_module("agent.application.prompts.insight_prompt_version")


def test_stable_and_changes_with_the_prompt(monkeypatch):
    first = insight_prompt_version()
    assert first == insight_prompt_version() and len(first) == 12
    monkeypatch.setattr(MODULE, "PLAN_SYSTEM", "다른 지시")
    assert insight_prompt_version() != first
