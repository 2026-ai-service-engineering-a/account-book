from __future__ import annotations

from dataclasses import dataclass

from .run_call import RunCall
from .run_line import RunLine


@dataclass(frozen=True, slots=True)
class RunDetail:
    """실행 하나와 그 도구 호출들 — 남은 순서 그대로."""

    line: RunLine
    calls: tuple[RunCall, ...]
