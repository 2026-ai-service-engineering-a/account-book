from __future__ import annotations

import asyncio
import dataclasses
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import date, tzinfo

from agent.application.dto import (
    LoopEvent,
    LoopLimits,
    LoopState,
    StopReason,
    ToolCall,
    ToolError,
    ToolPrompt,
    ToolResult,
    ToolStep,
    Turn,
)
from agent.application.errors import LedgerUnavailable, MalformedOutput, ModelUnavailable
from agent.application.ports import LanguageModel, LedgerApi
from agent.application.prompts import QUERY_SYSTEM, query_user_turn
from agent.domain.tools import CategoryLine, Mode, ToolName

from .run_tool import RunTool

_log = logging.getLogger(__name__)

_SERVER_RETRIES = 2  # internal_error를 코드가 다시 부르는 횟수. 스텝을 쓰지 않는다(agent-loop 7장)
_MERCHANT_TOOLS = {
    ToolName.SEARCH_TRANSACTIONS.value,
    ToolName.SUMMARIZE_SPENDING.value,
    ToolName.COUNT_FREQUENCY.value,
}


class AnswerQuestion:
    """기능 2의 흐름 — 짧은 ReAct(ai/agent-loop.md 4장).

    모델이 query 모드의 도구를 고르고, 실행기가 부르고, 봉투를 관찰로 돌려준다. 도구 없이
    답이 오면 끝난다. 그 밖의 정지 조건은 스텝·비용·벽시계 상한과 같은 (도구, 인자)의 반복.
    끊겨도 그때까지 모은 스텝을 낸다. 쓰기 도구는 목록에 없다 — 프롬프트가 아니라 목록으로 막는다.
    """

    def __init__(
        self,
        model: LanguageModel,
        ledger: LedgerApi,
        limits: LoopLimits,
        timer: Callable[[], float],
        pause: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._model = model
        self._ledger = ledger
        self._limits = limits
        self._timer = timer  # 단조 시계(초) — 벽시계 상한과 elapsed_ms
        self._pause = pause
        self._run_tool = RunTool(ledger, Mode.QUERY.tools, timer)

    async def __call__(self, question: str, today: date, zone: tzinfo) -> AsyncIterator[LoopEvent]:
        """`today`는 사용자 타임존의 오늘이다. 도구 이름을 흘리고, 끝에 실행 하나를 낸다."""
        state = LoopState(self._timer())
        try:
            dictionary = await self._ledger.categories()
        except LedgerUnavailable:
            yield self._finish(state, StopReason.LEDGER_UNAVAILABLE)
            return
        turns = [Turn("user", query_user_turn(question, today, dictionary))]
        prompt = ToolPrompt("query", QUERY_SYSTEM, (), Mode.QUERY.specs())
        while (stop := self._limit(state)) is None:
            try:
                reply = await self._model.complete_with_tools(
                    dataclasses.replace(prompt, turns=tuple(turns))
                )
            except MalformedOutput:
                state.calls += 1
                if state.malformed:
                    stop = StopReason.MALFORMED
                    break
                state.malformed = True  # 한 번은 다시 시킨다
                continue
            except ModelUnavailable:
                stop = StopReason.MODEL_UNAVAILABLE
                break
            state.calls += 1
            state.usage += reply.usage
            if not reply.tool_calls:
                yield self._finish(state, StopReason.ANSWERED, reply.text)
                return
            # 같이 온 글은 모델의 중간 생각이다. 대화에는 남기고 화면에는 보내지 않는다
            turns.append(Turn("assistant", reply.text, reply.tool_calls))
            for call in reply.tool_calls:
                if not state.first_time(call):
                    stop = StopReason.REPEATED
                    break
                yield LoopEvent(tool=call.name)
                result = await self._tool(call, dictionary, today, zone)
                state.steps.append(ToolStep(call, result))
                envelope = json.dumps(result.envelope(), ensure_ascii=False)
                turns.append(Turn("tool", envelope, call_id=call.call_id))
                if state.failed_too_often(call, result):
                    stop = StopReason.TOOL_FAILED
            if stop is not None:
                break
        yield self._finish(state, stop)

    async def _tool(
        self, call: ToolCall, dictionary: tuple[CategoryLine, ...], today: date, zone: tzinfo
    ) -> ToolResult:
        checked = _checked(call, dictionary)
        if isinstance(checked, ToolResult):
            return checked
        result = await self._run_tool(checked, today, zone)
        for attempt in range(1, _SERVER_RETRIES + 1):
            if result.error is None or result.error.code != "internal_error":
                break
            await self._pause(0.2 * attempt)  # 네트워크는 코드의 일이다 — 모델에게 넘기지 않는다
            result = await self._run_tool(checked, today, zone)
        return result

    def _limit(self, state: LoopState) -> StopReason | None:
        """다음 스텝을 밟기 전에 본다(ai/agent-loop.md 8장)."""
        if state.calls >= self._limits.max_steps:
            return StopReason.MAX_STEPS
        if state.usage.cost_usd >= self._limits.max_cost_usd:
            return StopReason.MAX_COST
        if self._timer() - state.started >= self._limits.wall_seconds:
            return StopReason.WALL_CLOCK
        return None

    def _finish(self, state: LoopState, stop: StopReason, text: str = "") -> LoopEvent:
        # 운영 로그 — 무엇에 걸려 끊겼는지. 발화·금액·가맹점은 넣지 않는다(development-rules 6.4)
        _log.info(
            "query run finished",
            extra={
                "stop": stop.value,
                "model_calls": state.calls,
                "tool_calls": len(state.steps),
                "input_tokens": state.usage.input_tokens,
                "output_tokens": state.usage.output_tokens,
                "cost_usd": round(state.usage.cost_usd, 6),
            },
        )
        return LoopEvent(outcome=state.end(stop, text))


def _checked(call: ToolCall, dictionary: tuple[CategoryLine, ...]) -> ToolCall | ToolResult:
    """사전 밖 category_id를 거른다(chat-analytics 6장·7.1).

    이름을 id 자리에 썼으면 id로 바꾸고, 가맹점을 받는 도구면 merchant로 찾게 바꾼다.
    그 밖이면 api를 부르지 않고 고칠 힌트를 담은 봉투를 돌려준다. 모델이 식별자를 지어내는
    것을 막는 자리다.
    """
    value = call.arguments.get("category_id")
    if not isinstance(value, str) or not value.strip():
        return call
    word = value.strip()
    if any(c.id == word for c in dictionary):
        return call
    arguments = dict(call.arguments)
    named = next((c.id for c in dictionary if c.name == word), None)
    if named is not None:
        arguments["category_id"] = named
        return dataclasses.replace(call, arguments=arguments)
    if call.name in _MERCHANT_TOOLS and not arguments.get("merchant"):
        del arguments["category_id"]
        arguments["merchant"] = word
        return dataclasses.replace(call, arguments=arguments)
    ids = ", ".join(c.id for c in dictionary)
    hint = f"category_id: 카테고리 사전에 없다. 사전의 id({ids})를 쓰거나 비운다"
    return ToolResult(call.call_id, error=ToolError("validation_error", True, hint))
