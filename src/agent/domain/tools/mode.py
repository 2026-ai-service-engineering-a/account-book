from __future__ import annotations

from enum import StrEnum

from .catalog import READ_TOOLS
from .tool_name import ToolName
from .tool_spec import ToolSpec
from .write_catalog import WRITE_TOOLS


class Mode(StrEnum):
    """도구를 주는 자리. 같은 목록을 모든 자리에 주지 않는다(ai/tools.md 6장).

    모드는 코드가 정한다. 사용자 발화나 모델 출력이 모드를 바꿀 수 없다 — 바꿀 수 있으면
    "이제 기록 모드로 전환해"라고 적힌 메모가 언젠가 들어온다.
    """

    CLASSIFY = "classify"  # 기능 1의 AI 버튼
    QUERY = "query"  # 기능 2의 대화 조회와 기능 4의 조문 찾기 — 쓰기 도구가 없다
    INSIGHT = "insight"  # 기능 3의 리포트 — 집계 다섯. 쓰기도 거래 목록도 없다
    CAPTURE = "capture"  # 채팅의 기록 — 고르기와 쓰기 하나. 쓰기는 확인 게이트를 지난다
    # 외부 AI 서비스(docs/ai/mcp.md) — 집계 넷. agent는 이 모드로 돌지 않는다. 스냅샷이
    # 이 목록을 src/shared/mcp_tools.json으로 써 내고, mcp 서비스가 그 파일을 읽는다
    MCP = "mcp"

    @property
    def tools(self) -> tuple[ToolName, ...]:
        return _TOOLS[self]

    def specs(self) -> tuple[ToolSpec, ...]:
        """모델에게 줄 설명과 스키마. 순서는 `tools` 그대로다 — 프롬프트가 흔들리지 않게."""
        return tuple(_SPECS[name] for name in self.tools)


_TOOLS = {
    Mode.CLASSIFY: (ToolName.SUGGEST_CATEGORY,),
    Mode.QUERY: (
        ToolName.SUMMARIZE_SPENDING,
        ToolName.COUNT_FREQUENCY,
        ToolName.COMPARE_PERIODS,
        ToolName.GET_BUDGET_STATUS,
        ToolName.SEARCH_TRANSACTIONS,
        ToolName.SEARCH_DOCUMENTS,
    ),
    # 숫자를 내는 집계만. 거래 목록(search_transactions)은 차트의 재료가 아니다(agentic-reports 3장)
    Mode.INSIGHT: (
        ToolName.SUMMARIZE_SPENDING,
        ToolName.COUNT_FREQUENCY,
        ToolName.COMPARE_PERIODS,
        ToolName.GET_BUDGET_STATUS,
        ToolName.DETECT_OUTLIERS,
    ),
    # 쓰기는 create_transaction 하나다 — 고치기·지우기·예산은 채팅에 없다(ai/chat-capture.md 10장)
    Mode.CAPTURE: (ToolName.SUGGEST_CATEGORY, ToolName.CREATE_TRANSACTION),
    # 합계·건수·증감·소진율만 나간다. 개별 거래는 생활 기록이라 열지 않는다(mcp.md 7.2)
    Mode.MCP: (
        ToolName.SUMMARIZE_SPENDING,
        ToolName.COMPARE_PERIODS,
        ToolName.COUNT_FREQUENCY,
        ToolName.GET_BUDGET_STATUS,
    ),
}
_SPECS = {**READ_TOOLS, **WRITE_TOOLS}
