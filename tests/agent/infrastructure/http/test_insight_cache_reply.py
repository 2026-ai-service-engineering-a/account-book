from __future__ import annotations

from agent.infrastructure.http.insight_cache_reply import InsightCacheReply


def test_a_miss_is_a_null_body():
    assert InsightCacheReply.model_validate({"key": "k", "body": None}).body is None
