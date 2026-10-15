from __future__ import annotations

import asyncio
import calendar
import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import date, tzinfo

from agent.application.dto import Insight, InsightState, InsightStop, Prompt, ToolCall, ToolStep
from agent.application.errors import MalformedOutput
from agent.application.parsers import parse_insight_draft, parse_plan
from agent.application.ports import LanguageModel, LedgerApi
from agent.application.prompts import insight_assembly_prompt, insight_plan_prompt
from agent.domain.tools import Mode, ToolName

from .chart_fill import fill_chart
from .highlight_check import kept_highlights
from .plan_check import checked_plan
from .retrieve import Retrieve
from .run_tool import RunTool

_log = logging.getLogger(__name__)

_ATTEMPTS = 2  # 스키마를 못 맞추면 한 번만 다시 시킨다(원칙 3)
MAX_CHARTS = 2  # 리포트의 나머지가 이미 고정 차트다(agentic-reports 10장)
# 처음 두 호출은 코드가 정한다 — 빈손 계획은 헛호출로 간다(agentic-reports 4장)
_FIXED = (
    ToolCall("call_1", ToolName.SUMMARIZE_SPENDING.value, {"period": "this_month"}),
    ToolCall("call_2", ToolName.GET_BUDGET_STATUS.value, {"period": "this_month"}),
)


class BuildInsights:
    """기능 3 — 상황에 맞는 통계. plan-and-execute다(ai/agent-loop.md 5장).

    고정 호출 둘 → 계획(LLM 1) → 검사한 단계를 동시에 → 조립(LLM 2) → 검증. 실행 결과가 전부
    비었을 때만 한 번 다시 계획한다(5.3). LLM 호출은 많아야 계획 2 + 조립 1이고 각자 한 번씩
    다시 시킬 수 있다. 집계는 계획마다 `max_calls - 2`까지다.
    버리는 단위는 차트 하나, 문장 하나다. 모델에 닿지 못하면 `ModelUnavailable`이 올라간다.

    벽시계 상한(agent-loop 8장 — 리포트 10초) 안에서 끝낸다. 추가 집계는 남은 시간의 절반까지만
    기다린다 — 나머지는 조립의 몫이다. 상한에 닿으면 빈 답(wall_clock)이다. 덜 보여줄 수 있어도
    늦으면 안 된다.
    """

    def __init__(
        self,
        model: LanguageModel,
        ledger: LedgerApi,
        retrieve: Retrieve,
        max_calls: int,
        timer: Callable[[], float],
        wall_seconds: float = 10.0,
    ) -> None:
        self._model = model
        self._wall = wall_seconds
        self._run_tool = RunTool(ledger, retrieve, Mode.INSIGHT.tools, timer)
        self._per_plan = max(max_calls - len(_FIXED), 0)

    async def __call__(self, month: date, today: date, zone: tzinfo) -> Insight:
        """`month`는 그 달 1일, `today`는 사용자 타임존의 오늘이다."""
        # 기준일을 그 달 안에 둔다 — 지난달 리포트에서 this_month가 그 달, last_month가 앞 달이다
        last = month.replace(day=calendar.monthrange(month.year, month.month)[1])
        reference, label = min(today, last), f"{month:%Y-%m}"
        run = InsightState()
        deadline = asyncio.get_running_loop().time() + self._wall
        try:
            async with asyncio.timeout_at(deadline):
                return await self._flow(run, label, reference, zone, deadline)
        except TimeoutError:
            return self._end(run, InsightStop.WALL_CLOCK)

    async def _flow(
        self, run: InsightState, label: str, reference: date, zone: tzinfo, deadline: float
    ) -> Insight:
        run.steps += await self._gather(_FIXED, reference, zone)
        if not all(s.result.ok for s in run.steps):
            return self._end(run, InsightStop.NO_BASE)
        empty_before: tuple[ToolStep, ...] = ()
        for _ in range(2):
            prompt = insight_plan_prompt(
                label, reference, Mode.INSIGHT.specs(), run.steps, self._per_plan, empty_before
            )
            raw = await self._ask(run, prompt, parse_plan)
            if raw is None:
                return self._end(run, InsightStop.MALFORMED)
            planned = checked_plan(
                raw, Mode.INSIGHT.tools, [s.call for s in run.steps], self._per_plan,
                len(run.steps) + 1,
            )  # fmt: skip
            run.whys |= {call.call_id: step.why for call, step in planned}
            if not planned:
                return self._end(run, InsightStop.NO_PLAN)
            ran = await self._gather([call for call, _ in planned], reference, zone, deadline)
            run.steps += ran
            if empty_before or not _all_empty(ran):
                break
            empty_before, run.replanned = tuple(ran), True
        assembly = insight_assembly_prompt(label, reference, run.steps)
        draft = await self._ask(run, assembly, parse_insight_draft)
        if draft is None:
            return self._end(run, InsightStop.MALFORMED)
        filled = (fill_chart(spec, run.steps) for spec in draft.charts)
        run.charts = tuple(c for c in filled if c is not None)[:MAX_CHARTS]
        run.highlights = kept_highlights(draft.highlights, run.steps, reference)
        stop = InsightStop.ASSEMBLED if run.charts or run.highlights else InsightStop.DISCARDED
        return self._end(run, stop, len(draft.charts) + len(draft.highlights))

    async def _gather(
        self,
        calls: Sequence[ToolCall],
        today: date,
        zone: tzinfo,
        deadline: float | None = None,
    ) -> list[ToolStep]:
        """서로 독립이라 동시에 부른다. 실패한 단계도 봉투다 — 그 단계만 비고 나머지로 간다.

        `deadline`이 있으면 남은 시간의 절반까지만 기다리고, 그때까지 끝나지 않은 단계는 버린다.
        """
        tasks = [asyncio.ensure_future(self._run_tool(c, today, zone)) for c in calls]
        if deadline is not None:
            left = (deadline - asyncio.get_running_loop().time()) / 2
            await asyncio.wait(tasks, timeout=max(left, 0))
            for task in tasks:
                task.cancel()  # 끝난 것에는 아무 일도 없다
        else:
            await asyncio.gather(*tasks)
        return [
            ToolStep(c, t.result())
            for c, t in zip(calls, tasks, strict=True)
            if t.done() and not t.cancelled()
        ]

    async def _ask[T](
        self, run: InsightState, prompt: Prompt, parse: Callable[[Mapping[str, object]], T]
    ) -> T | None:
        for _ in range(_ATTEMPTS):
            run.model_calls += 1
            try:
                return parse(await self._model.complete_json(prompt))
            except MalformedOutput:
                continue
        return None

    def _end(self, run: InsightState, stop: InsightStop, drafted: int = 0) -> Insight:
        # 운영 로그 — 개수만. 문장·가맹점·금액은 넣지 않는다(development-rules 6.4)
        _log.info(
            "insight finished stop=%s model_calls=%d tool_calls=%d drafted=%d kept=%d",
            stop.value,
            run.model_calls,
            len(run.steps),
            drafted,
            len(run.charts) + len(run.highlights),
        )
        return run.end(stop)


def _all_empty(steps: Sequence[ToolStep]) -> bool:
    """실패했거나 행이 0인 결과뿐인가 — 그때만 다시 계획한다(agent-loop 5.3)."""
    return all(
        not s.result.ok or (s.result.meta is not None and s.result.meta.row_count == 0)
        for s in steps
    )
