from __future__ import annotations

from .capture_request import CaptureRequest


class ChatRequest(CaptureRequest):
    """`POST /chat`의 본문 — 질문 한 줄과 기준 시각·타임존. 기록 한 줄과 모양이 같다.

    "저번 주"를 날짜로 푸는 기준이 이 `now`와 `timezone`이다. agent는 추측하지 않는다
    (development-rules 6.1).
    """
