from __future__ import annotations

from typing import Protocol


class DemoData(Protocol):
    """대역 저장소를 비우거나 예시로 채운다. 빈 화면을 눈으로 보려고 둔다.

    진짜 api가 붙으면 이 포트는 구현이 없다 — 화면에서 버튼이 사라진다.
    """

    async def reset(self, filled: bool) -> None: ...
