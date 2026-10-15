"""MCP 프로토콜의 겉 — 도구 목록과 도구 호출 둘만 연다(docs/ai/mcp.md 3장).

리소스·프롬프트·샘플링은 열지 않는다. 허용 목록 밖의 도구는 목록에도 없고, 불러도
없는 이름과 같은 응답을 받는다 — 있다는 것을 알면 바깥 모델이 그것을 부르려 한다(5장).
"""

from __future__ import annotations

import json
from collections.abc import Collection, Sequence
from typing import Any

import mcp_types as types
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.shared.exceptions import MCPError

from mcp_server.application.use_cases import CallTool
from mcp_server.domain.tools import ToolContract

NAME = "account-book"
INSTRUCTIONS = (
    "가계부의 집계를 읽는다 — 합계·건수·기간 비교·예산 소진율. 개별 거래는 보이지 않고 "
    "쓸 수도 없다. 기간은 이름(this_month·last_week…)으로 고른다. 날짜를 계산하지 않는다."
)
_CLIENT_LIMIT = 100  # 감사 로그의 client 칸
_READ_ONLY = types.ToolAnnotations(read_only_hint=True, open_world_hint=False)


def build_server(
    contract: Sequence[ToolContract], allowed: Collection[str], call: CallTool
) -> Server[Any]:
    """`contract` 중 `allowed`에 든 것만 내놓는다. 순서는 계약 그대로다."""
    exposed = {c.name.value: c for c in contract if c.name.value in allowed}
    listed = [
        types.Tool(
            name=c.name.value,
            description=c.description,
            input_schema=dict(c.input_schema),
            annotations=_READ_ONLY,
        )
        for c in exposed.values()
    ]

    async def list_tools(
        ctx: ServerRequestContext[Any], params: types.PaginatedRequestParams | None
    ) -> types.ListToolsResult:
        return types.ListToolsResult(tools=listed)

    async def call_tool(
        ctx: ServerRequestContext[Any], params: types.CallToolRequestParams
    ) -> types.CallToolResult:
        found = exposed.get(params.name)
        if found is None:  # 계약에 없는 이름과 목록 밖의 이름이 같은 길이다
            raise MCPError(types.INVALID_PARAMS, f"Unknown tool: {params.name}")
        envelope = await call(found.name, params.arguments or {}, _client(ctx))
        return types.CallToolResult(
            content=[types.TextContent(text=json.dumps(envelope, ensure_ascii=False))],
            structured_content=envelope,
            is_error=envelope["ok"] is not True,
        )

    return Server(NAME, instructions=INSTRUCTIONS, on_list_tools=list_tools, on_call_tool=call_tool)


def _client(ctx: ServerRequestContext[Any]) -> str:
    """초기화에서 클라이언트가 댄 이름. 대지 않았으면 unknown이다 — 지어내지 않는다."""
    params = ctx.session.client_params
    name = params.client_info.name.strip() if params is not None else ""
    return (name or "unknown")[:_CLIENT_LIMIT]
