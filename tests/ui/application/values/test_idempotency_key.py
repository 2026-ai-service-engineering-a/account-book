from __future__ import annotations

from ui.application.values import IdempotencyKey


def test_is_plain_text_at_runtime():
    # NewType은 타입 검사기에만 있다. 헤더·URL로 나갈 때 그대로 글자다.
    value = IdempotencyKey("01J9X:3")
    assert value == "01J9X:3" and isinstance(value, str)
