from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import litellm
import pytest

from agent.application.errors import ModelUnavailable
from agent.infrastructure.llm import LitellmEmbedder

EMBEDDER = LitellmEmbedder("gemini/gemini-embedding-001", "secret", dimensions=768, timeout=3)


def fake(monkeypatch, outcome: object) -> dict[str, Any]:
    seen: dict[str, Any] = {}

    async def aembedding(**kwargs: Any) -> object:
        seen.update(kwargs)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(litellm, "aembedding", aembedding)
    return seen


def test_vectors_in_order_with_dimensions_and_task(monkeypatch):
    seen = fake(monkeypatch, SimpleNamespace(data=[{"embedding": [1, 2]}, {"embedding": [3, 4]}]))
    assert asyncio.run(EMBEDDER.embed(["a", "b"])) == ((1.0, 2.0), (3.0, 4.0))
    assert seen["dimensions"] == 768 and seen["task_type"] == "SEMANTIC_SIMILARITY"
    assert seen["api_key"] == "secret"


def test_model_name_carries_the_dimensions():
    assert EMBEDDER.model == "gemini/gemini-embedding-001@768"


def test_nothing_to_embed_calls_nothing(monkeypatch):
    seen = fake(monkeypatch, RuntimeError("must not be called"))
    assert asyncio.run(EMBEDDER.embed([])) == () and seen == {}


@pytest.mark.parametrize(
    "outcome", [TimeoutError("slow"), SimpleNamespace(data=[{"embedding": [1]}])]
)
def test_failure_or_wrong_count_is_unavailable(monkeypatch, outcome):
    fake(monkeypatch, outcome)
    with pytest.raises(ModelUnavailable):
        asyncio.run(EMBEDDER.embed(["a", "b"]))
