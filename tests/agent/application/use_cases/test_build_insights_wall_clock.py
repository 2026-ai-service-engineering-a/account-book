"""벽시계 상한 — 늦은 리포트는 안 연다(agent-loop 8장). 빠른 시계를 쓰려고 상한을 짧게 준다."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping

from agent.application.dto import Insight, InsightStop, Prompt, TransactionFilter
from agent.application.use_cases import BuildInsights, Retrieve
from agent.domain.tools import OutlierReport
from tests.agent.application.use_cases.test_build_insights import (
    COMPARE,
    OUTLIERS,
    SEPTEMBER,
    TODAY,
    assembled,
    chart,
    ledger,
    plan,
)
from tests.agent.conftest import SEOUL, FakeEmbedder, FakeLedger, FakeModel


class SlowModel(FakeModel):
    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        await asyncio.sleep(0.2)
        return await super().complete_json(prompt)


class SlowOutliers(FakeLedger):
    async def outliers(self, where: TransactionFilter) -> OutlierReport:
        await asyncio.sleep(1.0)
        return await super().outliers(where)


def build(model: FakeModel, found: FakeLedger, wall: float) -> Insight:
    flow = BuildInsights(model, found, Retrieve(found, FakeEmbedder(), None), 6, lambda: 0.0, wall)
    return asyncio.run(flow(SEPTEMBER, TODAY, SEOUL))


def test_a_slow_model_ends_empty_at_the_wall_and_keeps_what_was_gathered():
    insight = build(SlowModel(plan(OUTLIERS), assembled([chart()])), ledger(), 0.1)
    assert insight.stop is InsightStop.WALL_CLOCK
    assert insight.charts == () and len(insight.steps) == 2  # 고정 호출은 감사 로그에 남는다


def test_a_slow_aggregate_is_left_out_and_the_rest_is_assembled():
    slow = SlowOutliers(replies=ledger().replies)
    insight = build(FakeModel(plan(OUTLIERS, COMPARE), assembled([chart()])), slow, 0.5)
    assert insight.stop is InsightStop.ASSEMBLED
    assert [s.call.name for s in insight.steps[2:]] == ["compare_periods"]
