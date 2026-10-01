from __future__ import annotations

import inspect

from agent.application.ports import LanguageModel
from agent.infrastructure.llm import LitellmLanguageModel
from tests.agent.conftest import FakeModel


def test_adapter_and_fake_fill_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    real: LanguageModel = LitellmLanguageModel("gemini/x", "key", timeout=1)
    fake: LanguageModel = FakeModel()
    assert inspect.iscoroutinefunction(real.complete_json)
    assert inspect.iscoroutinefunction(fake.complete_json)
