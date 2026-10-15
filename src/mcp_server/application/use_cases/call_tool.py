from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from zoneinfo import ZoneInfo

from mcp_server.application.dto import RunEntry
from mcp_server.application.errors import InvalidArguments, LedgerRejected, LedgerUnavailable
from mcp_server.application.parsers import parse_arguments
from mcp_server.application.policies import RateLimit
from mcp_server.application.ports import RunLog
from mcp_server.domain.tools import ToolName

from .run_aggregate import RunAggregate

_log = logging.getLogger(__name__)

type Envelope = dict[str, object]


class CallTool:
    """외부 클라이언트의 도구 호출 하나 — 상한을 보고, 인자를 검증하고, 집계를 부르고,
    봉투로 돌려주고, 감사 로그에 남긴다(docs/ai/mcp.md 7장).

    실패도 봉투다(ok: false). 프로토콜 오류로 올리지 않는다 — 바깥 모델이 읽고 인자를
    고칠 수 있어야 한다. 번역 표는 agent와 같다(docs/ai/tools.md 5장).
    상한에 걸린 호출은 api에 닿지 않고 감사 로그에도 남지 않는다 — 두드리는 것을 막는
    자리에서 DB에 한 줄씩 쓰면 막은 것이 아니다.
    """

    def __init__(
        self,
        run: RunAggregate,
        runs: RunLog,
        limit: RateLimit,
        clock: Callable[[], datetime],
        zone: ZoneInfo,
        timer: Callable[[], float],
        new_id: Callable[[], str],
    ) -> None:
        self._run = run
        self._runs = runs
        self._limit = limit
        self._clock = clock  # aware — 오늘을 사용자 타임존으로 정한다
        self._zone = zone
        self._timer = timer  # 초 단위 단조 시계 — elapsed_ms를 잰다
        self._new_id = new_id

    async def __call__(self, name: ToolName, args: Mapping[str, object], client: str) -> Envelope:
        run_id = self._new_id()
        wait = self._limit.take()
        if wait:
            _log.warning("mcp rate limited tool=%s retry_after=%d", name.value, wait)
            hint = f"분당 호출 상한을 넘었다. {wait}초 뒤에 다시 부른다"
            return _failure(run_id, "rate_limited", True, hint, retry_after_seconds=wait)
        started = self._timer()
        envelope = await self._envelope(run_id, name, args)
        elapsed = round((self._timer() - started) * 1000)
        meta = envelope.get("meta")
        if isinstance(meta, dict):
            meta["elapsed_ms"] = elapsed
        # 운영 로그에는 이름·결과 코드·시간만 — 인자와 숫자는 감사 로그에만(development-rules 6.4)
        _log.info(
            "mcp call run_id=%s tool=%s ok=%s ms=%d",
            run_id,
            name.value,
            envelope["ok"],
            elapsed,
        )
        await self._record(RunEntry(run_id, name.value, dict(args), envelope, client))
        return envelope

    async def _envelope(self, run_id: str, name: ToolName, args: Mapping[str, object]) -> Envelope:
        today = self._clock().astimezone(self._zone).date()
        try:
            request = parse_arguments(name, args)
            data, meta = await self._run(request, today, self._zone)
        except InvalidArguments as error:
            return _failure(run_id, "validation_error", True, f"{error.field}: {error.hint}")
        except LedgerRejected as error:
            return _rejection(run_id, error)
        except LedgerUnavailable:
            hint = "api에 닿지 못했다. 한 번만 다시 부를 수 있다"
            return _failure(run_id, "internal_error", True, hint)
        return {"call_id": run_id, "ok": True, "data": data, "meta": meta}

    async def _record(self, entry: RunEntry) -> None:
        """감사 기록이 실패해도 답은 나간다. 실패는 운영 로그에 run_id만 남긴다."""
        try:
            await self._runs.record(entry)
        except LedgerUnavailable as error:
            code = error.code if isinstance(error, LedgerRejected) else "unavailable"
            _log.warning("mcp run record failed run_id=%s code=%s", entry.run_id, code)


def _failure(call_id: str, code: str, retryable: bool, hint: str, **extra: object) -> Envelope:
    error: dict[str, object] = {"code": code, "retryable": retryable, "hint": hint} | extra
    return {"call_id": call_id, "ok": False, "error": error}


def _rejection(call_id: str, error: LedgerRejected) -> Envelope:
    """api의 거절을 모델이 읽을 실패로(docs/ai/tools.md 5장의 표)."""
    if error.code == "validation_error":
        fields = ", ".join(f"{k}: {v}" for k, v in error.details.items()) or "인자"
        return _failure(call_id, "validation_error", True, f"api가 인자를 거절했다 — {fields}")
    if error.code == "not_found":
        return _failure(call_id, "not_found", False, "찾는 것이 없다. 다시 찾지 않는다")
    return _failure(call_id, error.code, False, "api가 이 요청을 받지 않는다")
