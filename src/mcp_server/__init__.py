"""mcp — 외부 AI 클라이언트가 집계에 닿는 통로(docs/ai/mcp.md).

얇은 어댑터다. 판단도 프롬프트도 LLM 키도 DB도 없다 — 토큰을 보고, 계약(src/shared/
mcp_tools.json)의 도구를 내놓고, 호출을 api로 옮기고, 감사 로그에 남긴다. agent를 import하지
않는다(development-rules 2.3). 기간 풀이처럼 agent와 같은 일을 하는 코드는 여기 따로 있고,
같게 푸는지는 공유 사례표(tests/fixtures/shared/period_cases.json)가 맞춘다.
"""
