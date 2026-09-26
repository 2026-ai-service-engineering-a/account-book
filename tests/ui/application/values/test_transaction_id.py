from __future__ import annotations

from ui.application.values import TransactionId


def test_is_plain_text_at_runtime():
    # NewType은 타입 검사기에만 있다. 템플릿·URL로 나갈 때 그대로 글자다.
    value = TransactionId("t00001")
    assert value == "t00001" and isinstance(value, str)
