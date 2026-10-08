from __future__ import annotations

from agent.interfaces.schemas import ChunkBody
from tests.agent.application.use_cases.test_retrieve import CHUNK


def test_carries_the_source_and_the_original_text():
    body = ChunkBody.of(CHUNK).model_dump(mode="json")
    assert (body["title"], body["effective_date"], body["strategy"]) == (
        "할부거래에 관한 법률",
        "2026-09-08",
        "paragraph",
    )
