from __future__ import annotations

from collections.abc import Collection

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

AGGREGATES = "summarize_spending,compare_periods,count_frequency,get_budget_status"


class Settings(BaseSettings):
    """mcp가 환경변수를 읽는 유일한 자리(development-rules 6.3). docs/ai/mcp.md 6장.

    켜는 것은 사용자의 결정이다 — 기본은 꺼져 있다. 시크릿에는 기본값을 주지 않는다.
    """

    mcp_enabled: bool = False
    mcp_transport: str = "stdio"  # 지금은 stdio뿐이다. 노출 표면이 0이다
    mcp_token: SecretStr = SecretStr("")  # 비면 뜨지 않는다
    # 목록에 없는 도구는 목록 응답에도, 호출에도 없다. 집계 넷 밖은 이름을 적어도 뜨지 않는다
    mcp_allowed_tools: str = AGGREGATES
    mcp_calls_per_minute: int = Field(default=30, ge=1, le=600)

    user_timezone: str = "Asia/Seoul"
    api_base_url: str = "http://api:8000"

    # .env에는 다른 서비스의 변수도 있다. mcp가 쓰지 않는 것은 모른 척한다.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_tools(self) -> tuple[str, ...]:
        return tuple(n for n in (p.strip() for p in self.mcp_allowed_tools.split(",")) if n)

    def problems(self, offered: Collection[str]) -> list[str]:
        """뜨지 않을 이유. 비어 있으면 뜬다. `offered`는 계약에 있는 도구 이름이다."""
        found: list[str] = []
        if not self.mcp_enabled:
            found.append("MCP_ENABLED가 false다 — 켜는 것은 사용자의 결정이다")
        if not self.mcp_token.get_secret_value().strip():
            found.append("MCP_TOKEN이 비었다 — 토큰 없이 통로를 열지 않는다")
        if self.mcp_transport != "stdio":
            found.append(f"MCP_TRANSPORT={self.mcp_transport}는 아직 없다 — stdio만 된다")
        outside = [n for n in self.allowed_tools if n not in offered]
        if outside:
            names = ", ".join(sorted(offered))
            found.append(f"MCP_ALLOWED_TOOLS의 {', '.join(outside)}는 열 수 없다 — {names}만")
        if not self.allowed_tools:
            found.append("MCP_ALLOWED_TOOLS가 비었다")
        return found
