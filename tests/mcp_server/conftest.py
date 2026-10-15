from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from mcp_server.application.dto import LedgerFilter, RunEntry
from mcp_server.application.errors import LedgerUnavailable
from mcp_server.application.policies import RateLimit
from mcp_server.application.ports import Row
from mcp_server.application.use_cases import CallTool, RunAggregate
from mcp_server.domain.values import TimeRange

SEOUL = ZoneInfo("Asia/Seoul")
NOW = datetime(2026, 10, 15, 20, 0, tzinfo=SEOUL)  # 목요일
KRW = "KRW"


def won(amount: int) -> dict[str, object]:
    return {"amount": amount, "currency": KRW}


class FakeLedger:
    """api 자리. 받은 조건을 남기고, 정해 둔 줄을 낸다. `error`가 있으면 그것을 던진다."""

    def __init__(self, error: LedgerUnavailable | None = None, changes: int = 2) -> None:
        self.error = error
        self.changes = changes
        self.seen: list[object] = []

    async def summary(self, where: LedgerFilter) -> Row:
        self._called(where)
        return {"expense": won(412000), "income": won(0)}

    async def frequency(self, where: LedgerFilter) -> Row:
        self._called(where)
        return {"count": 3, "day_count": 3, "avg_gap_days": 2.5, "avg_amount": won(4800)}

    async def compare(self, a: TimeRange, b: TimeRange, category_id: str) -> list[Row]:
        self._called((a, b, category_id))
        return [
            {"category_id": f"c{i}", "name": "식비", "a": won(1), "b": won(2), "delta": won(1),
             "percent": 100}
            for i in range(self.changes)
        ]  # fmt: skip

    async def budget_status(self, month: date, category_id: str) -> list[Row]:
        self._called((month, category_id))
        return [{"category_id": "food", "name": "식비", "spent": won(300000)}]

    def _called(self, what: object) -> None:
        self.seen.append(what)
        if self.error is not None:
            raise self.error


class FakeRunLog:
    def __init__(self, error: LedgerUnavailable | None = None) -> None:
        self.error = error
        self.entries: list[RunEntry] = []

    async def record(self, entry: RunEntry) -> None:
        if self.error is not None:
            raise self.error
        self.entries.append(entry)


class Timer:
    """초 단위 단조 시계. 부를 때마다 `step`씩 간다."""

    def __init__(self, step: float = 0.0) -> None:
        self.now = 0.0
        self.step = step

    def __call__(self) -> float:
        self.now += self.step
        return self.now


def call_tool(
    ledger: FakeLedger | None = None,
    runs: FakeRunLog | None = None,
    per_minute: int = 30,
    timer: Timer | None = None,
) -> CallTool:
    ids = iter(f"run-{n}" for n in range(1, 1000))
    clock = timer or Timer()
    return CallTool(
        RunAggregate(ledger or FakeLedger()),
        runs or FakeRunLog(),
        RateLimit(per_minute, clock),
        lambda: NOW,
        SEOUL,
        clock,
        lambda: next(ids),
    )


@pytest.fixture(autouse=True)
def _no_mcp_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """dev 컨테이너는 .env를 환경으로 받는다. 거기 적힌 MCP_*가 테스트를 흔들지 않게 비운다."""
    for name in ("MCP_ENABLED", "MCP_TRANSPORT", "MCP_TOKEN", "MCP_ALLOWED_TOOLS",
                 "MCP_CALLS_PER_MINUTE"):  # fmt: skip
        monkeypatch.delenv(name, raising=False)
