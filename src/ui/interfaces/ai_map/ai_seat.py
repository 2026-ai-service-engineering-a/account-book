from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AiSeat:
    """AI가 들어가는 자리 하나. 화면의 AI 표시와 위키가 이것 하나를 같이 읽는다.

    내용의 정본은 docs/ai/다. 여기에는 표와 표시에 들어갈 것만 둔다.
    """

    key: str  # 위키 앵커 — /wiki#capture
    name: str
    feature: str  # docs/ai가 부르는 이름
    flow: str  # 표시에 들어갈 한 단어 — 단발 · ReAct · 계획 실행
    flow_detail: str
    llm_calls: str
    mode: str  # docs/ai/tools.md 6장의 도구 모드
    tools: tuple[str, ...]
    replaces: str  # 사람이 손으로 하던 판단
    screens: tuple[tuple[str, str], ...]  # (이름, 경로)
    human: str  # 사람이 끼는 자리
    fallback: str  # 못 할 때
    port: str  # ui가 아는 포트
    stand_in: str  # 지금 그 자리에 서 있는 각본 대역
    stand_in_does: str
    doc: str
