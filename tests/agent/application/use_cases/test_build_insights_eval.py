"""리포트 평가 — 실제 모델로 세 세트를 돈다(docs/ai/agentic-reports.md 9장).

도구 응답은 tests/fixtures/ai/reports/의 고정값이다 — DB 없이 모델의 판단만 잰다. 돈이 들고 매번
조금씩 다르다. CI에서 돌지 않는다(docs/ai/README.md 5장).

    make eval-insights   # make dev로 agent가 떠 있어야 한다(키가 거기 있다)

프롬프트나 도구 설명을 고치면 이걸 돌려 나온 표를 커밋 메시지에 남긴다. 지표는 검증 전 초안으로
잰다 — 검증이 버려 주는 것까지 모델의 실력으로 세지 않는다.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from agent.application.dto import Insight, ModelReply, Prompt, ToolPrompt
from agent.application.parsers import parse_insight_draft
from agent.application.use_cases import BuildInsights, Retrieve
from agent.application.use_cases.chart_fill import fill_chart
from agent.application.use_cases.highlight_check import SCOLDING
from agent.application.use_cases.number_check import numbers_from_tools, unsupported
from agent.domain.tools import (
    BudgetLine,
    CategoryShift,
    Frequency,
    OutlierLine,
    OutlierReport,
    SkippedLine,
    SpendingTotals,
)
from agent.domain.values import Amount, CategoryId, TimeRange
from agent.infrastructure.llm import LitellmLanguageModel
from agent.infrastructure.settings import Settings
from tests.agent.conftest import FakeEmbedder, FakeLedger

SETS = Path(__file__).parents[3] / "fixtures" / "ai" / "reports"
ZONE = ZoneInfo("Asia/Seoul")
TODAY = date(2026, 10, 15)
RUNS = 2  # 같은 입력을 두 번 — 재현성
# 평범한 달에 "변화"를 말한 문장 — 억지 발견으로 센다
_CHANGE = re.compile(r"늘|증가|급증|줄|감소|넘|초과|특이|평소|눈에 띄")

pytestmark = pytest.mark.integration


class RecordingModel:
    """진짜 모델을 감싸 조립 호출의 초안(검증 전)을 남긴다."""

    def __init__(self, real: LitellmLanguageModel) -> None:
        self._real = real
        self.model = real.model
        self.drafts: list[Mapping[str, object]] = []

    async def complete_json(self, prompt: Prompt) -> Mapping[str, object]:
        raw = await self._real.complete_json(prompt)
        if prompt.name == "insight":
            self.drafts.append(raw)
        return raw

    async def complete_with_tools(self, prompt: ToolPrompt) -> ModelReply:
        raise AssertionError("리포트는 도구 호출 응답을 쓰지 않는다")


@dataclass(frozen=True)
class Run:
    name: str
    insight: Insight
    drafted_charts: int
    drafted_lines: list[str]
    dropped: list[str]  # 버려진 차트 — 프롬프트를 어디서 고칠지 보인다
    seconds: float


def _amount(value: int | None) -> Amount | None:
    return Amount(value) if value is not None else None


# 고정 세트(JSON)를 도구 응답으로. 파일을 읽는 경계라 Any다(development-rules 5.2)
def ledger(replies: dict[str, Any]) -> FakeLedger:
    s, o, f = replies["summary"], replies["outliers"], replies["frequency"]
    lines = tuple(
        BudgetLine(
            CategoryId(b["category_id"]),
            b["name"],
            Amount(b["spent"]),
            _amount(b["limit"]),
            _amount(b["remaining"]),
            b["percent"],
            None,
            None,
        )
        for b in replies["budget_status"]
    )
    shifts = tuple(
        CategoryShift(
            CategoryId(c["category_id"]),
            c["name"],
            Amount(c["a"]),
            Amount(c["b"]),
            Amount(c["delta"]),
            c["percent"],
        )
        for c in replies["compare"]
    )
    items = tuple(
        OutlierLine(
            i["id"],
            datetime.fromisoformat(i["occurred_at"]),
            CategoryId(i["category_id"]),
            i["merchant"],
            Amount(i["amount"]),
            Amount(i["usual_median"]),
            Amount(i["usual_upper"]),
        )
        for i in o["items"]
    )
    baseline = TimeRange(
        datetime.fromisoformat(o["baseline_from"]), datetime.fromisoformat(o["baseline_to"])
    )
    skipped = tuple(SkippedLine(CategoryId(k["category_id"]), k["reason"]) for k in o["skipped"])
    frequency = Frequency(f["count"], f["day_count"], f["avg_gap_days"], Amount(f["avg_amount"]))
    return FakeLedger(
        replies={
            "summary": SpendingTotals(Amount(s["expense"]), Amount(s["income"])),
            "budget_status": lines,
            "compare": shifts,
            "outliers": OutlierReport(baseline, items, o["truncated"], skipped),
            "frequency": frequency,
        }
    )


def run_once(name: str, case: dict[str, Any], real: LitellmLanguageModel) -> Run:
    model = RecordingModel(real)
    found = ledger(case["replies"])
    flow = BuildInsights(model, found, Retrieve(found, FakeEmbedder(), None), 6, time.perf_counter)
    month = date.fromisoformat(f"{case['month']}-01")
    started = time.perf_counter()
    insight = asyncio.run(flow(month, TODAY, ZONE))
    seconds = time.perf_counter() - started
    charts, lines, dropped = 0, [], []
    for raw in model.drafts:
        draft = parse_insight_draft(raw)
        charts += len(draft.charts)
        lines += [h.text for h in draft.highlights]
        tools = {s.call.call_id: s.call.name for s in insight.steps}
        dropped += [
            f"{c.kind}/{c.unit} {tools.get(c.source, c.source)}.{c.x_field}·{c.y_field}"
            for c in draft.charts
            if fill_chart(c, insight.steps) is None
        ]
    return Run(name, insight, charts, lines, dropped, seconds)


def _said(run: Run) -> str:
    labels = " ".join(p.label for c in run.insight.charts for p in c.points)
    return " ".join(run.insight.highlights) + " " + labels


def test_report_insights_on_the_three_sets():
    settings = Settings()
    real = LitellmLanguageModel(
        settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
    )
    cases = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(SETS.glob("*.json"))}
    runs = [run_once(name, case, real) for name, case in cases.items() for _ in range(RUNS)]
    drafted = sum(r.drafted_charts for r in runs)
    kept = sum(len(r.insight.charts) for r in runs)
    lines = [(r, line) for r in runs for line in r.drafted_lines]
    scolding = [line for _, line in lines if any(w in line for w in SCOLDING)]
    unbacked = [
        line
        for r, line in lines
        if unsupported(line, numbers_from_tools(r.insight.steps, date(2026, 9, 30)))
    ]
    forced = [line for r in runs if r.name == "ordinary" for line in r.insight.highlights
              if _CHANGE.search(line)]  # fmt: skip
    latencies = sorted(r.seconds for r in runs)

    print(f"\n== 리포트 평가 ({settings.agent_model}, 세트 {len(cases)}개, 세트마다 {RUNS}회)")
    print(f"스펙 유효율     {kept}/{drafted}")
    print(f"금지어          {len(scolding)}건")
    print(f"숫자 일치율     {len(lines) - len(unbacked)}/{len(lines)} (초안 문장)")
    print(f"억지 발견       {len(forced)}건 (평범한 달에 남은 변화 문장)")
    for name, case in cases.items():
        mine = [r for r in runs if r.name == name]
        caught = [any(m in _said(r) for m in case["expect"].get("mentions", [])) for r in mine]
        specs = {
            json.dumps([(c.kind, c.unit, [p.label for p in c.points]) for c in r.insight.charts])
            for r in mine
        }
        print(f"  [{name}] 끝 {[r.insight.stop.value for r in mine]} 짚음 {caught} "
              f"같은 스펙 {len(specs) == 1}")  # fmt: skip
        for r in mine:
            for line in r.insight.highlights:
                print(f"    - {line}")
    print(f"p95 지연         {latencies[max(int(len(latencies) * 0.95) - 1, 0)]:.1f}s")
    for line in scolding + unbacked:
        print(f"  걸림: {line}")
    for r in runs:
        for spec in r.dropped:
            print(f"  버린 차트 [{r.name}]: {spec}")

    assert not scolding, "훈계가 초안에 있다 — 검증이 버렸어도 프롬프트를 고칠 일이다"
    assert drafted == 0 or kept / drafted >= 0.95, "스펙 유효율이 95% 아래다"
    for name in ("big_one", "new_category"):
        mentions = cases[name]["expect"]["mentions"]
        assert any(any(m in _said(r) for m in mentions) for r in runs if r.name == name), name
