from __future__ import annotations

from enum import StrEnum


class Permission(StrEnum):
    """도구가 무엇을 할 수 있나(ai/tools.md 2장). 쓰기는 확인을 거친다(README 4장)."""

    READ = "read"
    WRITE_CONFIRM = "write_confirm"  # 확인 필요. 금액 임계값은 api가 본다
    WRITE_ALWAYS_CONFIRM = "write_always_confirm"
