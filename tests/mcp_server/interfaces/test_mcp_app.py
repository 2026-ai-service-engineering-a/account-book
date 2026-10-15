from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import mcp_types as types
import pytest
from mcp import Client
from mcp.shared.exceptions import MCPError

from mcp_server.infrastructure.contract_file import CONTRACT, read_contract
from mcp_server.infrastructure.settings import AGGREGATES
from mcp_server.interfaces import build_server
from tests.mcp_server.conftest import FakeLedger, FakeRunLog, call_tool

ALL = AGGREGATES.split(",")


def connect[T](
    use: Callable[[Client], Awaitable[T]],
    allowed: list[str] = ALL,
    runs: FakeRunLog | None = None,
    mode: str = "legacy",
    name: str = "Claude Desktop",
) -> T:
    server = build_server(read_contract(), allowed, call_tool(FakeLedger(), runs))
    info = types.Implementation(name=name, version="1.0")

    async def go() -> T:
        async with Client(server, mode=mode, client_info=info) as client:
            return await use(client)

    return asyncio.run(go())


def test_what_is_open_to_the_outside_is_the_contract():
    """여기에 줄이 늘면 외부에 열린 표면이 늘어난 것이다(docs/ai/mcp.md 8장).
    도구의 이름·설명·스키마는 src/shared/mcp_tools.json 그대로다 — 그 파일은 agent의
    스냅샷 테스트가 고정한다."""

    async def listed(client: Client) -> list[dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "input_schema": t.input_schema}
            for t in (await client.list_tools()).tools
        ]

    assert connect(listed) == json.loads(Path(CONTRACT).read_text(encoding="utf-8"))


def test_every_tool_is_marked_read_only():
    async def hints(client: Client) -> set[object]:
        return {
            (t.annotations.read_only_hint if t.annotations else None)
            for t in (await client.list_tools()).tools
        }

    assert connect(hints) == {True}


def test_a_tool_off_the_list_is_absent_from_the_list_and_from_calls():
    # 목록에서만 숨기고 호출은 되는 구현이 흔한 실수다(mcp.md 8장)
    allowed = ["count_frequency"]

    async def names(client: Client) -> list[str]:
        return [t.name for t in (await client.list_tools()).tools]

    assert connect(names, allowed) == ["count_frequency"]

    async def refused(client: Client) -> list[str]:
        messages = []
        for name in ("summarize_spending", "search_transactions", "no_such_tool"):
            with pytest.raises(MCPError) as caught:
                await client.call_tool(name, {"period": "this_month"})
            messages.append(caught.value.message.replace(name, "?"))
        return messages

    # 목록 밖의 도구도, 우리에게 있지만 열지 않은 도구도, 없는 도구와 똑같이 답한다
    assert len(set(connect(refused, allowed))) == 1


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_a_call_answers_and_is_recorded_with_the_clients_name(mode):
    runs = FakeRunLog()

    async def answered(client: Client) -> types.CallToolResult:
        return await client.call_tool("summarize_spending", {"period": "this_month"})

    result = connect(answered, runs=runs, mode=mode)
    assert result.is_error is False
    assert result.structured_content["data"]["expense"]["amount"] == 412000
    assert json.loads(result.content[0].text) == result.structured_content  # type: ignore[union-attr]
    assert [e.client for e in runs.entries] == ["Claude Desktop"]


def test_a_tool_error_is_a_flag_on_the_result_not_a_protocol_error():
    async def wrong(client: Client) -> types.CallToolResult:
        return await client.call_tool("summarize_spending", {"period": "저번 주"})

    result = connect(wrong)
    assert result.is_error is True
    assert result.structured_content["error"]["code"] == "validation_error"


def test_an_unnamed_client_is_recorded_as_unknown():
    runs = FakeRunLog()

    async def answered(client: Client) -> types.CallToolResult:
        return await client.call_tool("count_frequency", {"period": "today"})

    connect(answered, runs=runs, name="  ")
    assert runs.entries[0].client == "unknown"
