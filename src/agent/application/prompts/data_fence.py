"""바깥에서 온 문자열을 경계 마커로 감싼다(docs/ai/README.md 2장 원칙 5)."""

from __future__ import annotations

OPEN = "<<<DATA"
CLOSE = "DATA>>>"


def fence(text: str) -> str:
    """마커를 닫고 나오는 게 가장 쉬운 탈출이라, 안에 든 마커는 먼저 지운다.

    지우고 나서 새 마커가 생길 수 있다("<<<DA<<<DATATA"). 더 지울 게 없을 때까지 지운다.
    """
    cleaned = text
    while OPEN in cleaned or CLOSE in cleaned:
        cleaned = cleaned.replace(OPEN, "").replace(CLOSE, "")
    return f"{OPEN}\n{cleaned}\n{CLOSE}"
