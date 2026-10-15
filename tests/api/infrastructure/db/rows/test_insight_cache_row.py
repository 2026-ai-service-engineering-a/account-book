from __future__ import annotations

from api.infrastructure.db.rows import InsightCacheRow


def test_maps_the_insight_cache_table():
    assert InsightCacheRow.__tablename__ == "insight_cache"
