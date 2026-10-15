from __future__ import annotations

from typing import Any

from pydantic import SecretStr

from mcp_server.infrastructure.settings import AGGREGATES, Settings

OFFERED = set(AGGREGATES.split(","))


def settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {"mcp_enabled": True, "mcp_token": SecretStr("t" * 32)}
    return Settings(_env_file=None, **(values | overrides))


def test_off_by_default():
    found = Settings(_env_file=None)
    assert not found.mcp_enabled and found.allowed_tools == tuple(AGGREGATES.split(","))
    assert len(found.problems(OFFERED)) == 2  # 꺼져 있고 토큰이 없다


def test_an_enabled_server_with_a_token_starts():
    assert settings().problems(OFFERED) == []


def test_an_empty_or_blank_token_keeps_it_closed():
    for token in ("", "   "):
        (problem,) = settings(mcp_token=SecretStr(token)).problems(OFFERED)
        assert "MCP_TOKEN" in problem


def test_only_stdio_for_now():
    (problem,) = settings(mcp_transport="http").problems(OFFERED)
    assert "stdio만" in problem


def test_tools_outside_the_four_aggregates_cannot_be_allowed():
    # 범위 밖 — 이름을 적어도 열리지 않는다. 조용히 무시하지 않고 뜨지 않는다
    allowed = "summarize_spending, search_transactions,propose_transaction"
    (problem,) = settings(mcp_allowed_tools=allowed).problems(OFFERED)
    assert "search_transactions, propose_transaction" in problem


def test_the_list_may_narrow_but_not_be_empty():
    assert settings(mcp_allowed_tools=" count_frequency ,").allowed_tools == ("count_frequency",)
    (problem,) = settings(mcp_allowed_tools=" , ").problems(OFFERED)
    assert "비었다" in problem
