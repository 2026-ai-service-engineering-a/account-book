from __future__ import annotations

import asyncio
from datetime import datetime

from agent.application.dto import InsightStop
from agent.application.errors import LedgerUnavailable
from agent.application.use_cases import BuildInsights, CachedInsights, Retrieve
from agent.domain.values import TimeRange
from tests.agent.application.use_cases.test_build_insights import (
    OUTLIERS,
    SAID,
    SEPTEMBER,
    TODAY,
    assembled,
    chart,
    ledger,
    plan,
)
from tests.agent.conftest import SEOUL, FakeEmbedder, FakeInsightCache, FakeLedger, FakeModel


def cached(
    model: FakeModel, found: FakeLedger, cache: FakeInsightCache, name: str = "gemini/flash"
) -> CachedInsights:
    build = BuildInsights(model, found, Retrieve(found, FakeEmbedder(), None), 6, lambda: 0.0)
    return CachedInsights(build, found, cache, name)


def answer() -> FakeModel:
    return FakeModel(plan(OUTLIERS), assembled([chart()], SAID))


def test_the_second_time_is_free_and_the_same():
    cache, found = FakeInsightCache(), ledger()
    first = asyncio.run(cached(answer(), found, cache)(SEPTEMBER, TODAY, SEOUL))
    silent = FakeModel()  # 부르면 터진다 — 두 번째는 모델을 부르지 않아야 한다
    second = asyncio.run(cached(silent, found, cache)(SEPTEMBER, TODAY, SEOUL))
    assert second.stop is InsightStop.CACHED and silent.prompts == []
    assert (second.charts, second.highlights) == (first.charts, first.highlights)


def test_the_version_is_read_over_the_month_and_the_six_before_it():
    found = ledger()
    asyncio.run(cached(answer(), found, FakeInsightCache())(SEPTEMBER, TODAY, SEOUL))
    (window,) = [args[0] for method, args in found.calls if method == "data_version"]
    assert window == TimeRange(
        datetime(2026, 3, 1, tzinfo=SEOUL), datetime(2026, 10, 1, tzinfo=SEOUL)
    )


def test_a_new_version_or_model_or_month_is_a_new_key():
    cache = FakeInsightCache()
    asyncio.run(cached(answer(), ledger(), cache)(SEPTEMBER, TODAY, SEOUL))
    asyncio.run(cached(answer(), ledger(data_version="v2"), cache)(SEPTEMBER, TODAY, SEOUL))
    asyncio.run(cached(answer(), ledger(), cache, "openai/x")(SEPTEMBER, TODAY, SEOUL))
    assert len(cache.rows) == 3


def test_failures_and_timeouts_are_not_kept():
    cache = FakeInsightCache()
    asyncio.run(cached(FakeModel(plan()), ledger(), cache)(SEPTEMBER, TODAY, SEOUL))
    assert len(cache.rows) == 1  # 볼 것이 없다(no_plan)는 같은 입력에 같은 답이라 담는다
    broken = ledger(budget_status=LedgerUnavailable("down"), data_version="v9")
    asyncio.run(cached(FakeModel(), broken, cache)(SEPTEMBER, TODAY, SEOUL))
    assert len(cache.rows) == 1  # 고정 호출 장애(no_base)는 담지 않는다


def test_the_cache_is_an_accelerator_not_a_dependency():
    down = LedgerUnavailable("ConnectError")
    found = asyncio.run(cached(answer(), ledger(), FakeInsightCache(down))(SEPTEMBER, TODAY, SEOUL))
    assert found.stop is InsightStop.ASSEMBLED
    unversioned = ledger(data_version=down)
    found = asyncio.run(cached(answer(), unversioned, FakeInsightCache())(SEPTEMBER, TODAY, SEOUL))
    assert found.stop is InsightStop.ASSEMBLED


def test_a_body_that_cannot_be_read_is_made_again():
    cache, found = FakeInsightCache(), ledger()
    asyncio.run(cached(answer(), found, cache)(SEPTEMBER, TODAY, SEOUL))
    (key,) = cache.rows
    cache.rows[key] = {"charts": "?", "highlights": []}
    again = asyncio.run(cached(answer(), found, cache)(SEPTEMBER, TODAY, SEOUL))
    assert again.stop is InsightStop.ASSEMBLED
