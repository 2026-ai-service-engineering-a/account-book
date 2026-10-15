"""조립 지점. 설정을 읽고, 뜨지 않을 이유가 있으면 stderr에 적고 끝낸다.

    python -m mcp_server.main      # 클라이언트가 띄운다 — stdin·stdout이 프로토콜이다

stdout은 프로토콜의 자리다. 로그는 stderr로만 나간다.
"""

from __future__ import annotations

import logging
import sys
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import anyio
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from mcp_server.application.policies import RateLimit
from mcp_server.application.use_cases import CallTool, RunAggregate
from mcp_server.infrastructure.contract_file import read_contract
from mcp_server.infrastructure.http import HttpLedgerApi, HttpRunLog
from mcp_server.infrastructure.settings import Settings
from mcp_server.interfaces import build_server

# api 호출 하나의 상한. 집계는 DB가 하니 금방이다
_API_TIMEOUT = 5.0
# 감사 기록 하나의 상한. 기록을 기다리느라 답이 늦어지면 안 된다
_RECORD_TIMEOUT = 2.0


def create_server(settings: Settings) -> Server[object] | list[str]:
    """뜰 수 있으면 서버를, 아니면 뜨지 않을 이유를 낸다."""
    contract = read_contract()
    problems = settings.problems({c.name.value for c in contract})
    if problems:
        return problems
    zone = ZoneInfo(settings.user_timezone)
    call = CallTool(
        RunAggregate(HttpLedgerApi(settings.api_base_url, _API_TIMEOUT)),
        HttpRunLog(settings.api_base_url, _RECORD_TIMEOUT),
        RateLimit(settings.mcp_calls_per_minute, time.monotonic),
        lambda: datetime.now(zone),
        zone,
        time.monotonic,
        lambda: str(uuid.uuid4()),
    )
    return build_server(contract, settings.allowed_tools, call)


def main() -> int:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s")
    # httpx는 요청 URL을 INFO로 찍는다 — 가맹점으로 좁히면 q=가 운영 로그에 남는다(6.4)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    server = create_server(Settings())
    if isinstance(server, list):
        for problem in server:
            print(f"mcp가 뜨지 않는다: {problem}", file=sys.stderr)
        return 2

    async def serve() -> None:
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    anyio.run(serve)
    return 0


if __name__ == "__main__":
    sys.exit(main())
