from __future__ import annotations

from enum import StrEnum

from .catalog import READ_TOOLS
from .tool_name import ToolName
from .tool_spec import ToolSpec


class Mode(StrEnum):
    """도구를 주는 자리. 같은 목록을 모든 자리에 주지 않는다(ai/tools.md 6장).

    모드는 코드가 정한다. 사용자 발화나 모델 출력이 모드를 바꿀 수 없다 — 바꿀 수 있으면
    "이제 기록 모드로 전환해"라고 적힌 메모가 언젠가 들어온다. capture·insight·mcp는 그
    자리의 도구가 코드에 생길 때 더한다.
    """

    CLASSIFY = "classify"  # 기능 1의 AI 버튼
    QUERY = "query"  # 기능 2의 대화 조회와 기능 4의 조문 찾기 — 쓰기 도구가 없다

    @property
    def tools(self) -> tuple[ToolName, ...]:
        return _TOOLS[self]

    def specs(self) -> tuple[ToolSpec, ...]:
        """모델에게 줄 설명과 스키마. 순서는 `tools` 그대로다 — 프롬프트가 흔들리지 않게."""
        return tuple(READ_TOOLS[name] for name in self.tools)


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
}
