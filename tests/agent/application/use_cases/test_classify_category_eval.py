"""카테고리 고르기 평가 — 실제 모델과 떠 있는 api(지금은 ui의 api 대역)를 부른다.

돈이 들고 매번 점수가 조금씩 다르다. CI에서 돌지 않는다(docs/ai/README.md 5장).

    make eval      # make dev로 ui·agent가 떠 있어야 한다

프롬프트나 임계값을 고치면 이걸 돌려 나온 표를 커밋 메시지에 남긴다.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

from agent.application.dto import ClassifyThresholds
from agent.application.ports import LanguageModel
from agent.application.use_cases import ClassifyCategory
from agent.domain.values import ChoiceStrategy, Direction
from agent.infrastructure.http import HttpLedgerApi
from agent.infrastructure.llm import LitellmEmbedder, LitellmLanguageModel
from agent.infrastructure.settings import Settings
from tests.agent.conftest import FakeModel

FIXTURE = Path(__file__).parents[3] / "fixtures" / "ai" / "classify.json"
ABSTAIN = {
    "category_id": "",
    "evidence_ids": [],
    "reason": "",
    "abstain": True,
    "self_confidence": 0.0,
}

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class Outcome:
    group: str
    expected: str | None
    chosen: str | None
    strategy: ChoiceStrategy
    seconds: float

    @property
    def right(self) -> bool:
        return self.chosen == self.expected

    @property
    def confident_wrong(self) -> bool:
        """골랐는데 틀렸다. 사용자 신뢰를 깎는 건 이것뿐이다(9장)."""
        return self.chosen is not None and not self.right


def run(use_case: ClassifyCategory) -> list[Outcome]:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]

    async def one(case: dict[str, str | None]) -> Outcome:
        started = time.perf_counter()
        direction = Direction(case.get("direction") or "expense")
        choice = await use_case(str(case["merchant"]), "", direction)
        return Outcome(
            str(case["group"]),
            case["expected"],
            choice.category_id,
            choice.strategy,
            time.perf_counter() - started,
        )

    async def all_cases() -> list[Outcome]:
        return [await one(case) for case in cases]  # 하나씩 — 지연을 재야 한다

    return asyncio.run(all_cases())


def report(title: str, outcomes: list[Outcome]) -> None:
    n = len(outcomes)
    latencies = sorted(o.seconds for o in outcomes)
    strategies = Counter(o.strategy.value for o in outcomes)
    print(f"\n== {title} ({n}건)")
    print(f"top-1 정확도     {sum(o.right for o in outcomes) / n:.0%}")
    print(f"자신 있는 오답률 {sum(o.confident_wrong for o in outcomes) / n:.0%}")
    print(f"abstain율        {strategies['none'] / n:.0%}")
    print(f"건당 LLM 호출    {strategies['llm'] / n:.2f}")
    print(f"p95 지연         {latencies[int(n * 0.95) - 1]:.1f}s")
    print(f"길별             {dict(strategies)}")
    for group in ("frequent", "new", "ambiguous"):
        part = [o for o in outcomes if o.group == group]
        print(f"  {group:9s} 정확 {sum(o.right for o in part)}/{len(part)}", end="")
        print(f"  틀림 {[(o.chosen, o.expected) for o in part if o.confident_wrong]}")


def assemble(model: LanguageModel) -> ClassifyCategory:
    settings = Settings()
    thresholds = ClassifyThresholds(
        settings.classify_min_confidence, settings.classify_abstain_below
    )
    embedder = LitellmEmbedder(
        settings.embedding_model,
        settings.api_key(settings.embedding_model),
        dimensions=settings.embedding_dimensions,
        timeout=settings.agent_timeout_seconds,
    )
    ledger = HttpLedgerApi(settings.api_base_url, timeout=settings.agent_timeout_seconds)
    return ClassifyCategory(ledger, model, thresholds, embedder)


def test_baseline_and_with_llm():
    """기준선(0~2단계만)을 먼저 잰다. 3단계를 붙여서 의미 있게 올라가지 않으면 붙이지 않는다."""
    settings = Settings()
    baseline = run(assemble(FakeModel(*[ABSTAIN] * 100)))  # LLM 자리에서 늘 모른다고 한다
    report("기준선 — 규칙·이력·벡터만", baseline)
    model = LitellmLanguageModel(
        settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
    )
    full = run(assemble(model))
    report(f"LLM까지 — {settings.agent_model}", full)
    # 자주 가는 곳은 0·1·2단계가 잡아야 한다. 여기서 LLM이 돌면 설계가 틀린 것이다(9장).
    frequent = [o for o in full if o.group == "frequent"]
    assert all(o.strategy is not ChoiceStrategy.LLM for o in frequent)
    assert all(o.right for o in frequent)
