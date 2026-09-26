from __future__ import annotations

import inspect

from ui.application.ports import CaptureReader
from ui.infrastructure.scripted import ScriptedCaptureReader


def test_stand_in_fills_the_port():
    # 대입이 곧 계약 검사다 — 시그니처가 어긋나면 mypy가 여기서 막는다
    port: CaptureReader = ScriptedCaptureReader(delay=0)
    assert inspect.iscoroutinefunction(port.read)
