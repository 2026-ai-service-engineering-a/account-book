"""대화 통계 평가 — 실제 모델과 떠 있는 api를 부른다(docs/ai/chat-analytics.md 9장).

돈이 들고 매번 점수가 조금씩 다르다. CI에서 돌지 않는다(docs/ai/README.md 5장).

    make eval-chat      # make dev로 api·agent가 떠 있어야 한다

프롬프트나 도구 설명을 고치면 이걸 돌려 나온 표를 커밋 메시지에 남긴다.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from agent.application.dto import LoopLimits, LoopOutcome, RetrievalDefaults
from agent.application.parsers import parse_tool_arguments
from agent.application.use_cases import AnswerQuestion, Retrieve, SyncIndex
from agent.application.use_cases.number_check import numbers_from_tools, unsupported
from agent.domain.tools import ToolName
from agent.domain.values import ChunkStrategy, PeriodName, PeriodSpec, SearchMode
from agent.infrastructure.http import HttpLedgerApi
from agent.infrastructure.llm import LitellmEmbedder, LitellmLanguageModel
from agent.infrastructure.settings import Settings

FIXTURE = Path(__file__).parents[3] / "fixtures" / "ai" / "questions.json"
ZONE = ZoneInfo("Asia/Seoul")
_REFUSALS = ("못", "없", "어렵", "알 수 없")

pytestmark = pytest.mark.integration


@dataclass(frozen=True)
class Graded:
    group: str
    question: str
    tool_right: bool
    period_right: bool | None  # 기간을 라벨로 단 질문만
    numbers_right: bool  # 모델이 쓴 문장의 숫자가 전부 도구에서 왔나(7.2)
    refused: bool | None  # 거절해야 하는 질문만
    model_calls: int
    seconds: float


def expected_period(label: dict[str, object], today: date) -> PeriodSpec:
    name = PeriodName(str(label["name"]))
    if "months_ago" in label:
        month = today.month - int(str(label["months_ago"]))
        year = today.year + (month - 1) // 12
        return PeriodSpec(name, start=date(year, (month - 1) % 12 + 1, 1))
    if "month_of_year" in label:
        return PeriodSpec(name, start=date(today.year, int(str(label["month_of_year"])), 1))
    if "start_md" in label:
        start = date.fromisoformat(f"{today.year}-{label['start_md']}")
        end = date.fromisoformat(f"{today.year}-{label['end_md']}")
        return PeriodSpec(name, start=start, end=end)
    return PeriodSpec(name, days=int(str(label.get("days", 0))))


def grade(case: dict[str, object], outcome: LoopOutcome, today: date, seconds: float) -> Graded:
    steps = [s for s in outcome.steps if s.result.ok]
    group = str(case["group"])
    tool_right, period_right, refused = False, None, None
    if group in ("single", "period") and steps:
        call = steps[0].call
        tool_right = call.name == case["tool"]
        if tool_right:
            parsed = parse_tool_arguments(ToolName(call.name), call.arguments)
            keys = [k for k in ("period", "a", "b") if k in case]
            period_right = all(
                getattr(parsed, k) == expected_period(case[k], today)  # type: ignore[arg-type]
                for k in keys
            )
            if "category_id" in case:
                tool_right = getattr(parsed, "category_id", None) == case["category_id"]
            if "merchant" in case:
                tool_right = str(case["merchant"]) in getattr(parsed, "merchant", "")
        elif group == "period":
            period_right = False
    elif group == "period":
        period_right = False
    elif group == "pair":
        wanted = case["tools"]
        tool_right = isinstance(wanted, list) and set(wanted) <= {s.call.name for s in steps}
    elif group == "refuse":
        tool_right = True
        refused = any(word in outcome.text for word in _REFUSALS)
    numbers_right = not unsupported(outcome.text, numbers_from_tools(outcome.steps, today))
    return Graded(
        group,
        str(case["question"]),
        tool_right,
        period_right,
        numbers_right,
        refused,
        outcome.model_calls,
        seconds,
    )


def run(loop: AnswerQuestion, today: date) -> list[Graded]:
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]

    async def one(case: dict[str, object]) -> Graded:
        started = time.perf_counter()
        events = [e async for e in loop(str(case["question"]), today, ZONE)]
        outcome = events[-1].outcome
        assert outcome is not None
        return grade(case, outcome, today, time.perf_counter() - started)

    async def all_cases() -> list[Graded]:
        return [await one(case) for case in cases]  # 하나씩 — 지연을 재야 한다

    return asyncio.run(all_cases())


def report(title: str, graded: list[Graded]) -> None:
    n = len(graded)
    periods = [g.period_right for g in graded if g.period_right is not None]
    refusals = [g.refused for g in graded if g.refused is not None]
    latencies = sorted(g.seconds for g in graded)
    print(f"\n== {title} ({n}건)")
    print(f"도구 선택 정확도 {sum(g.tool_right for g in graded)}/{n}")
    print(f"기간 해석 정확도 {sum(periods)}/{len(periods)}")
    print(f"숫자 일치율     {sum(g.numbers_right for g in graded)}/{n}")
    print(f"거절률          {sum(bool(r) for r in refusals)}/{len(refusals)}")
    print(f"건당 LLM 호출    {sum(g.model_calls for g in graded) / n:.2f}")
    print(f"p95 지연         {latencies[int(n * 0.95) - 1]:.1f}s")
    for g in graded:
        if not g.tool_right or g.period_right is False or not g.numbers_right or g.refused is False:
            print(f"  틀림 [{g.group}] {g.question}")


def test_questions_become_the_right_tool_calls():
    settings = Settings()
    model = LitellmLanguageModel(
        settings.agent_model, settings.api_key(), timeout=settings.agent_timeout_seconds
    )
    ledger = HttpLedgerApi(settings.api_base_url, timeout=settings.agent_timeout_seconds)
    embedder = LitellmEmbedder(
        settings.embedding_model,
        settings.api_key(settings.embedding_model),
        dimensions=settings.embedding_dimensions,
        timeout=settings.agent_timeout_seconds,
    )
    defaults = RetrievalDefaults(
        ChunkStrategy(settings.doc_chunk_strategy),
        SearchMode(settings.doc_search_mode),
        settings.doc_top_k,
    )
    retrieve = Retrieve(ledger, embedder, SyncIndex(ledger, embedder), defaults)
    limits = LoopLimits(settings.agent_max_steps, settings.agent_max_cost_usd, 20.0)
    today = datetime.now(ZONE).date()
    loop = AnswerQuestion(model, ledger, retrieve, limits, time.perf_counter)
    graded = run(loop, today)
    report(f"대화 통계 — {settings.agent_model}", graded)
    # 기간이 틀리면 숫자가 전부 틀리고 사용자는 알아채지 못한다(9장). 여기만 100%를 요구한다.
    periods = [g.period_right for g in graded if g.period_right is not None]
    assert all(periods), "기간 해석이 틀린 질문이 있다"
