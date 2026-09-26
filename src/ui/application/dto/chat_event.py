from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .proposal import Proposal

ChatEventKind = Literal["token", "tool", "proposal", "message", "error", "done"]


@dataclass(frozen=True, slots=True)
class ChatEvent:
    """agent가 SSE로 보내는 이벤트 하나(chat.md 4.1).

    `tool`에는 도구 이름만 싣는다. 인자는 싣지 않는다.
    """

    kind: ChatEventKind
    text: str = ""
    proposal: Proposal | None = None
    code: str = ""  # error일 때만
