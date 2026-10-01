from __future__ import annotations

from agent.application.ports import Embedder
from agent.infrastructure.llm import LitellmEmbedder
from tests.agent.conftest import FakeEmbedder


def test_adapter_and_fake_fill_the_port():
    real: Embedder = LitellmEmbedder("gemini/x", "key", dimensions=768, timeout=1)
    fake: Embedder = FakeEmbedder()
    assert real.model == "gemini/x@768" and fake.model
