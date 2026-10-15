from __future__ import annotations

from api.interfaces.schemas import InsightCacheBody


def test_a_miss_is_a_null_body():
    assert InsightCacheBody(key="k", body=None).model_dump() == {"key": "k", "body": None}
