"""AI가 들어가는 자리 넷. docs/ai의 기능 셋에 "기록"을 더한 것이다.

기록(capture)은 docs/ai/agent-loop.md 3장과 tools.md 6장에 흐름·모드로만 있고 기능 문서는
따로 없다. 화면에서는 가장 먼저 만나는 자리라 목록 맨 앞에 둔다.
"""

from __future__ import annotations

from .ai_seat import AiSeat

SEATS: tuple[AiSeat, ...] = (
    AiSeat(
        key="capture",
        name="기록",
        feature="기록 (capture)",
        flow="단발",
        flow_detail="단발 + 확인 게이트",
        llm_calls="1회",
        mode="capture",
        tools=(
            "suggest_category",
            "search_transactions",
            "create_transaction",
            "update_transaction",
            "delete_transaction",
            "set_budget",
        ),
        replaces="문장이나 카드 문자를 보며 날짜·금액·가맹점을 칸마다 옮겨 치기",
        screens=(("채팅 — 기록 문장", "/"), ("거래 입력 — 한 줄로 채우기", "/transactions/new")),
        human="채팅은 확인 카드, 폼은 저장 버튼. 확인 전에는 아무것도 쓰지 않는다",
        fallback="못 읽으면 칸을 바꾸지 않고 못 읽었다고 한다",
        port="ChatAgent · CaptureReader",
        stand_in="ScriptedChatAgent · ScriptedCaptureReader",
        stand_in_does="정해진 모양의 한 줄과 카드 승인 문자 한 모양만 읽는다",
        doc="docs/ai/agent-loop.md 3장 · tools.md 6장",
        live=(
            "한 줄로 채우기는 agent의 POST /capture가 LLM으로 읽는다. 날짜 계산과 가맹점 검사는"
            " 코드가 한다. 채팅은 아직 각본 대역"
        ),
    ),
    AiSeat(
        key="classify",
        name="카테고리 고르기",
        feature="기능 1 · RAG",
        flow="단발",
        flow_detail="단발 — 규칙 표 → 이력 → 벡터 이웃, 그래도 애매하면 LLM 한 번",
        llm_calls="0~1회",
        mode="classify",
        tools=("suggest_category",),
        replaces="드롭다운에서 카테고리 고르기",
        screens=(("거래 입력 — 카테고리", "/transactions/new"),),
        human="AI로 고르기를 누를 때만 고른다. 근거 한 줄을 같이 보여 주고, 저장이 확인이다",
        fallback="신뢰도가 낮으면 모른다고 하고 사람이 고른다",
        port="CategorySuggester",
        stand_in="ScriptedCategorySuggester",
        stand_in_does="가맹점명의 낱말 표 하나로 고른다 — 0단계 규칙 표 흉내",
        doc="docs/ai/category-suggestion-rag.md",
        live=(
            "AI로 고르기와 한 줄로 채우기가 agent의 POST /classify로 고른다. api가 규칙·이력·"
            "pgvector 이웃으로 찾고, 애매할 때만 LLM이 근거를 보고 하나를 고른다"
        ),
    ),
    AiSeat(
        key="query",
        name="대화로 묻는 통계",
        feature="기능 2",
        flow="ReAct",
        flow_detail="짧은 ReAct — 도구를 고르고, 결과를 보고, 한 줄로 읽는다",
        llm_calls="2~4회",
        mode="query",
        tools=(
            "summarize_spending",
            "count_frequency",
            "compare_periods",
            "get_budget_status",
            "search_transactions",
        ),
        replaces="화면과 필터를 옮겨 다니며 세기",
        screens=(("채팅 — 질문", "/"),),
        human="쓰기 도구를 아예 주지 않는다. 조회가 기록을 바꿀 길이 없다",
        fallback="스텝 상한에 닿으면 '여기까지 해봤어요'와 지금까지의 답",
        port="ChatAgent",
        stand_in="ScriptedChatAgent",
        stand_in_does="'얼마'·'?'가 든 질문에 리포트 합계로 답한다",
        doc="docs/ai/chat-analytics.md",
    ),
    AiSeat(
        key="insight",
        name="상황에 맞는 통계",
        feature="기능 3",
        flow="계획 실행",
        flow_detail="plan-and-execute — 고정 호출 2회 → 계획 → 집계 동시 호출 → 조립",
        llm_calls="2회",
        mode="insight",
        tools=(
            "summarize_spending",
            "compare_periods",
            "count_frequency",
            "get_budget_status",
            "detect_outliers",
        ),
        replaces="고정 차트를 눈으로 훑으며 이번 달에 볼 것 고르기",
        screens=(("리포트 — 눈에 띈 것", "/reports"),),
        human="읽기만 한다. 문장의 숫자는 도구 결과의 값만 쓴다",
        fallback="검증에 실패하면 고정 리포트만 보여 준다",
        port="ReportNarrator",
        stand_in="ScriptedReportNarrator",
        stand_in_does="늘어난 카테고리와 예산 페이스를 규칙 문구로 — 그림 고르기는 아직 고정",
        doc="docs/ai/agentic-reports.md",
    ),
)

BY_KEY: dict[str, AiSeat] = {seat.key: seat for seat in SEATS}
