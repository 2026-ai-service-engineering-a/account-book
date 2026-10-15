from __future__ import annotations

import logging
from typing import Any

from mcp.server.lowlevel import Server
from pydantic import SecretStr

from mcp_server.infrastructure.settings import Settings
from mcp_server.main import create_server, main


def settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {"mcp_enabled": True, "mcp_token": SecretStr("t" * 32)}
    return Settings(_env_file=None, **(values | overrides))


def test_starts_when_enabled_with_a_token():
    assert isinstance(create_server(settings()), Server)


def test_without_a_token_it_does_not_start():
    found = create_server(settings(mcp_token=SecretStr("")))
    assert isinstance(found, list) and "MCP_TOKEN" in found[0]


def test_main_says_why_on_stderr_and_exits(monkeypatch, capsys):
    monkeypatch.setenv("MCP_ENABLED", "false")
    monkeypatch.setenv("MCP_TOKEN", "")
    monkeypatch.chdir("/")  # 저장소의 .env를 읽지 않게
    assert main() == 2
    captured = capsys.readouterr()
    assert captured.out == ""  # stdout은 프로토콜의 자리다
    assert "mcp가 뜨지 않는다: MCP_ENABLED가 false다" in captured.err


def test_request_urls_stay_out_of_the_log(monkeypatch):
    # 가맹점으로 좁힌 호출의 URL에는 q=가 있다 — httpx의 요청 로그를 끈다(development-rules 6.4)
    monkeypatch.chdir("/")
    monkeypatch.setattr(logging.getLogger("httpx"), "level", logging.NOTSET)
    main()
    assert logging.getLogger("httpx").level == logging.WARNING
